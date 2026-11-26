## Question

![](/assets/q_indexing.png)

## Response Section

**Database index** คือโครงสร้างข้อมูลเพิ่มเติมที่ DB สร้างแยกจากตาราง เพื่อหาแถวที่ต้องการได้โดยไม่ต้องอ่านทั้งตาราง เปรียบเหมือน **สารบัญท้ายเล่มของหนังสือ** ที่บอกว่าคำนี้อยู่หน้าไหน ทำให้ไม่ต้องเปิดอ่านทุกหน้า

ส่วนใหญ่เป็น **B-tree** ซึ่งเก็บค่าของ column เรียงลำดับไว้พร้อมตำแหน่งของแถว ทำให้หาข้อมูลได้ใน **O(log n)** แทนการ full table scan ที่เป็น **O(n)** เช่น ตาราง 10 ล้านแถว B-tree ใช้แค่ราว 3–4 ระดับก็เจอ นอกจากนี้ยังมีแบบอื่น เช่น Hash (เท่ากับเท่านั้น), GIN (full-text, JSON, array) และ BRIN (ข้อมูลที่เรียงตามเวลา)

### ข้อดี

1. **อ่านข้อมูลเร็วขึ้นมาก** เมื่อใช้กับ `WHERE`, `JOIN ... ON`, `ORDER BY`, `GROUP BY`
   - `WHERE email = 'a@b.com'` ไม่ต้องไล่ทุกแถว
   - `JOIN` ด้วย foreign key ที่มี index ไม่ต้อง scan ตารางลูกทุกครั้ง
   - `ORDER BY created_at LIMIT 20` อ่านจาก index ที่เรียงไว้แล้วได้เลย ไม่ต้อง sort ใหม่
2. **บังคับให้ข้อมูลไม่ซ้ำ** ด้วย unique index เช่น email ห้ามซ้ำ ซึ่ง DB รับประกันได้แม้มี request เข้ามาพร้อมกัน (การเช็คในแอปอย่างเดียวกัน race condition ไม่ได้)
3. **Covering index** ถ้า index มีทุก column ที่ query ต้องการ DB ตอบได้จาก index เลยโดยไม่ต้องกลับไปอ่านตาราง (index-only scan)
4. **ลดภาระของระบบโดยรวม** query เร็วขึ้นทำให้ใช้ CPU และ I/O น้อยลง ถือ lock สั้นลง และรองรับผู้ใช้พร้อมกันได้มากขึ้น

### ข้อจำกัด

1. **เขียนข้อมูลช้าลง (write overhead)** ทุก `INSERT`, `UPDATE` และ `DELETE` DB ต้องอัปเดต index ทุกตัวที่เกี่ยวข้องด้วย ยิ่งมี index มาก การเขียนยิ่งช้า ตารางที่เขียนบ่อยมาก เช่น log หรือ event จึงควรมี index เท่าที่จำเป็น
2. **ใช้พื้นที่เพิ่ม** index ใช้ทั้ง disk และ memory (buffer cache) บางครั้งขนาดรวมของ index ใหญ่กว่าตัวตารางเอง และแย่ง cache กับข้อมูลจริง
3. **ไม่ได้ช่วยทุกกรณี**
   - **Column ที่ค่าซ้ำกันมาก (low selectivity)** เช่น `gender` หรือ `is_active` ถ้า query คืนข้อมูลเป็นสัดส่วนใหญ่ของตาราง optimizer จะเลือก full scan เพราะเร็วกว่าการกระโดดไปมาตาม index
   - **ตารางเล็ก** อ่านทั้งตารางเร็วกว่าการเปิด index อยู่แล้ว
4. **บาง query ใช้ index ไม่ได้** แม้มี index อยู่
   - `LIKE '%abc'` (wildcard นำหน้า) เพราะ B-tree เรียงจากตัวอักษรตัวแรก
   - ครอบ column ด้วย function หรือการคำนวณ เช่น `WHERE LOWER(email) = ...` หรือ `WHERE YEAR(created_at) = 2026` ต้องใช้ expression index หรือเขียน query เป็นช่วงแทน
   - **Composite index ใช้ได้ตามลำดับจากซ้าย (leftmost prefix)** index `(school_id, grade, room)` ใช้กับ `WHERE school_id = 1` ได้ แต่ใช้กับ `WHERE grade = 1` อย่างเดียวไม่ได้ ลำดับของ column จึงสำคัญ
   - type ไม่ตรงกันจนเกิด implicit cast เช่น เทียบ column ชนิด varchar กับตัวเลข
5. **ต้องดูแลต่อเนื่อง** index ที่ไม่มี query ใช้แล้ว (unused index) ยังทำให้เขียนช้าอยู่ index บวม (bloat) จากการ update และ delete บ่อย และการสร้าง index บนตารางใหญ่อาจ lock ตาราง ต้องใช้วิธีอย่าง `CREATE INDEX CONCURRENTLY`

### สรุปแนวทาง

ควรสร้าง index ตาม **query ที่ใช้จริง** ไม่ใช่สร้างทุก column ให้ดูจาก `EXPLAIN` / `EXPLAIN ANALYZE` ว่า query ใช้ index หรือไม่ แล้วเลือก column ที่ใช้ filter หรือ join บ่อยและมีค่าหลากหลาย (high selectivity) โดยคำนึงถึงการแลกกันระหว่าง **อ่านเร็วขึ้น กับเขียนช้าลงและใช้พื้นที่เพิ่ม**

**ตัวอย่างจากส่วนที่ 4 ของข้อสอบนี้**
- `UniqueConstraint(fields=['school', 'grade', 'room'])` สร้าง **composite unique index** ให้ ทั้งกันห้องซ้ำ และทำให้ query `WHERE school_id = ?` เร็วขึ้นด้วย เพราะ `school` อยู่ซ้ายสุด
- Django สร้าง index ให้ **foreign key** ทุกตัวอัตโนมัติ (`classroom_id`, `school_id`) จึงทำให้ filter `?school=` / `?classroom=` และการ join เร็ว
- filter `first_name` แบบ `icontains` สร้างเป็น `LIKE '%...%'` ซึ่ง **B-tree index ช่วยไม่ได้** ถ้าข้อมูลเยอะจริงต้องใช้ trigram index (`pg_trgm`) หรือ full-text search
