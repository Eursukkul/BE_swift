"""
เขียบนโปรแกรมแปลงตัวเลยเป็นคำอ่านภาษาไทย

[Input]
number: positive number rang from 0 to 10_000_000

[Output]
num_text: string of thai number call

[Example 1]
input = 101
output = หนึ่งร้อยเอ็ด

[Example 2]
input = -1
output = number can not less than 0
"""


class Solution:
    DIGITS = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
    PLACES = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน"]

    def number_to_thai(self, number: int) -> str:
        if number < 0:
            return "number can not less than 0"
        if number > 10_000_000:
            return "number can not more than 10,000,000"
        if number == 0:
            return "ศูนย์"
        return self._read(number, False)

    def _read(self, number: int, has_prefix: bool) -> str:
        if number >= 1_000_000:
            millions, rest = divmod(number, 1_000_000)
            return self._read(millions, False) + "ล้าน" + self._read(rest, True)

        s = str(number)
        text = ""
        for i, ch in enumerate(s):
            place, d = len(s) - 1 - i, int(ch)
            if d == 0:
                continue
            if place == 0 and d == 1 and (number >= 10 or has_prefix):
                text += "เอ็ด"
            elif place == 1 and d == 1:
                text += "สิบ"
            elif place == 1 and d == 2:
                text += "ยี่สิบ"
            else:
                text += self.DIGITS[d] + self.PLACES[place]
        return text
