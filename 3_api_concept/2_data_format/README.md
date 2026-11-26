## Question

![](/assets/q_data_format.png)

## Response Section

JSON และ Protocol Buffers (Protobuf) เป็น **รูปแบบการ serialize ข้อมูล (data format)** คือวิธีแปลงข้อมูลในโปรแกรมให้เป็น bytes เพื่อส่งผ่าน network หรือเก็บลงไฟล์ เป็นคนละระดับกับรูปแบบของ API อย่าง REST หรือ gRPC แม้ปกติ REST จะใช้คู่กับ JSON และ gRPC ใช้คู่กับ Protobuf แต่ก็ส่ง Protobuf ผ่าน REST หรือส่ง JSON ผ่าน gRPC ได้

### ตัวอย่างข้อมูลชุดเดียวกัน

**JSON** เป็น text ที่บรรจุทั้งชื่อ field และค่าไว้ในตัวเอง (self-describing)

```json
{"id":1,"name":"Tom","age":30,"is_active":true}
```
→ **47 bytes**

**Protobuf** ต้องประกาศ schema ไว้ล่วงหน้าในไฟล์ `.proto` แล้วใช้ `protoc` generate code ของแต่ละภาษา

```protobuf
syntax = "proto3";

message User {
  int32  id        = 1;   // ตัวเลขคือ field number ที่ส่งไปบน wire แทนชื่อ field
  string name      = 2;
  int32  age       = 3;
  bool   is_active = 4;
}
```
ข้อมูลเดียวกันเมื่อ encode เป็น binary:
```
08 01  12 03 54 6f 6d  18 1e  20 01
└id=1┘ └─name="Tom"──┘ └age=30┘ └active┘
```
→ **11 bytes** (เล็กกว่าประมาณ 4 เท่า) เพราะไม่ต้องส่งชื่อ field เครื่องหมาย `"` `:` `,` และตัวเลขถูกเก็บเป็น varint (เลข 30 ใช้แค่ 1 byte)

### เปรียบเทียบ

| หัวข้อ | JSON | Protobuf |
|---|---|---|
| รูปแบบ | Text (UTF-8) | Binary |
| คนอ่านได้ | ✅ อ่านและแก้ได้ทันที | ❌ ต้องมี `.proto` และเครื่องมือช่วย decode |
| Schema | ไม่บังคับ (ใช้ JSON Schema หรือ OpenAPI เสริมได้) | **บังคับ** ต้องมี `.proto` ทั้งฝั่งส่งและฝั่งรับ |
| ขนาด | ใหญ่ เพราะส่งชื่อ field ซ้ำทุก record | เล็ก โดยทั่วไปเล็กกว่า JSON หลายเท่า |
| ความเร็ว encode/decode | ช้ากว่า เพราะต้อง parse text และแปลงตัวเลขจาก string | เร็วกว่า เพราะอ่าน binary ตามตำแหน่งได้เลย |
| ชนิดข้อมูล | มีแค่ string, number, bool, null, array, object ไม่มี int64 และวันที่ที่ชัดเจน | strict type เช่น `int32`, `int64`, `double`, `bool`, `bytes`, `enum`, nested message, `repeated` |
| เปลี่ยน schema | ยืดหยุ่น เพิ่ม field ได้ทันที แต่ถ้าเปลี่ยนชื่อหรือชนิดอาจพังโดยไม่มีใครรู้จนถึง runtime | ออกแบบมาให้ **backward และ forward compatible** ผ่าน field number โดยฝั่งที่ใช้ schema เก่าจะข้าม field ใหม่ไป |
| Tooling | ทุกภาษามีในตัว, browser ใช้ได้ทันที, debug ด้วย curl หรือ DevTools | ต้องติดตั้ง `protoc` และ generate code, browser ใช้ตรงๆ ไม่ได้ |
| Type safety ในโค้ด | ต้อง validate เอง เช่น serializer หรือ pydantic | ได้ class ที่มี type จาก code generation |

### ข้อดีและข้อเสียของ JSON

**ข้อดี**
- **อ่านง่ายและ debug ง่าย** เปิดดู log, response หรือ payload แล้วเข้าใจได้ทันที
- **ใช้ได้ทุกที่** ทุกภาษามีในตัว browser ใช้ได้ทันที (`fetch`, `JSON.parse`) และเป็นมาตรฐานของ public API
- **ไม่ต้องมีขั้นตอน build** ไม่ต้อง generate code ทั้งสองฝั่งพัฒนาแยกกันได้
- **ยืดหยุ่น** เหมาะกับข้อมูลที่โครงสร้างยังเปลี่ยนบ่อยหรือไม่แน่นอน

**ข้อเสีย**
- **ขนาดใหญ่** ชื่อ field ถูกส่งซ้ำทุก record ใน list 10,000 รายการ ชื่อ field ก็ถูกส่ง 10,000 ครั้ง
- **parse ช้ากว่าและใช้ CPU มากกว่า** เห็นผลชัดเมื่อมี traffic มาก
- **ชนิดข้อมูลไม่ชัด** ตัวเลขทุกตัวเป็น `number` เลขที่เกิน 2^53 จะเสียความแม่นยำใน JavaScript (ต้องส่ง id ขนาด int64 เป็น string) ไม่มีชนิดวันที่ ต้องตกลงกันเองว่าใช้ ISO 8601 และ binary ต้องแปลงเป็น base64 ซึ่งทำให้ขนาดโตขึ้นประมาณ 33%
- **ไม่มี contract บังคับ** ถ้า server เปลี่ยนชื่อ field client จะพังตอน runtime โดยไม่มีอะไรเตือนก่อน

### ข้อดีและข้อเสียของ Protobuf

**ข้อดี**
- **เล็กและเร็ว** ประหยัด bandwidth และ CPU เหมาะกับการสื่อสารระหว่าง service ที่มี traffic สูง, mobile ที่ใช้ network ช้า และ IoT
- **มี contract ชัดเจน** `.proto` เป็นทั้งเอกสารและ type definition ที่ทุกฝั่งใช้ร่วมกัน ความไม่ตรงกันถูกจับได้ตั้งแต่ตอน compile
- **generate code ได้หลายภาษา** ทั้ง Go, Java, Python, C# และอื่นๆ จากไฟล์เดียว ลดการเขียน model และ validation ซ้ำ
- **เปลี่ยน schema ได้อย่างปลอดภัย** เพิ่ม field ใหม่ได้โดยไม่ทำให้ client เก่าพัง เพราะฝั่งที่ใช้ schema เก่าจะข้าม field number ที่ไม่รู้จักไป

**ข้อเสีย**
- **คนอ่านไม่ได้** debug ยากกว่า ดู payload ใน log หรือ network tab ไม่ได้โดยตรง ต้องใช้เครื่องมือช่วย เช่น `protoc --decode` หรือ grpcurl
- **ต้องมีขั้นตอน build และแชร์ `.proto`** ต้องจัดการ version ของ schema ระหว่างทีม และถ้า schema ไม่ตรงกันจะ decode ผิด
- **มีกฎที่ต้องระวัง** ห้ามนำ field number เดิมไปใช้ซ้ำหรือเปลี่ยนชนิด (ต้องใช้ `reserved`) และใน proto3 ค่า default เช่น `0`, `""` และ `false` แยกไม่ออกว่าไม่ได้ส่งมาหรือส่งมาเป็นค่านั้น ถ้าต้องแยกต้องใช้ `optional` หรือ wrapper type
- **รองรับใน browser น้อย** ต้องใช้ library เพิ่ม เช่น gRPC-Web หรือ protobuf.js และ ecosystem ของ public API ส่วนใหญ่คาดหวัง JSON

### สรุป: เลือกใช้เมื่อไร

| สถานการณ์ | ควรใช้ | เหตุผล |
|---|---|---|
| Public API, web frontend, third-party integration | **JSON** | ทุก client ใช้ได้ทันที อ่านง่าย มีเอกสารและเครื่องมือมาก |
| Config, log, งานที่คนต้องอ่านหรือแก้ | **JSON** | อ่านได้โดยตรง |
| Internal service-to-service ที่มี traffic สูง | **Protobuf** | ประหยัด CPU และ bandwidth ได้ contract ร่วมกัน |
| Mobile app ที่ network ช้าหรือคิดค่า data | **Protobuf** | payload เล็ก |
| Streaming หรือข้อมูลปริมาณมาก (event, telemetry) | **Protobuf** | encode และ decode เร็ว ขนาดเล็ก |

ทั้งสองแบบไม่มีตัวไหนดีกว่าในทุกกรณี เป็นการแลกกันระหว่าง **ความสะดวกและความเข้ากันได้ (JSON)** กับ **ประสิทธิภาพและ type safety (Protobuf)** ระบบจริงจำนวนมากใช้ทั้งสองแบบ คือ JSON สำหรับ API ที่เปิดให้ภายนอกใช้ และ Protobuf ระหว่าง service ภายใน

ตัวอย่างในส่วนที่ 4 ของข้อสอบนี้ใช้ JSON (`JSONParser` / `JSONRenderer`) ซึ่งเหมาะแล้ว เพราะเป็น REST API ที่ client ทั่วไปและ browsable API ต้องอ่านได้
