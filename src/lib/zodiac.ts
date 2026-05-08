const ZODIAC_RANGES: Array<[[number, number], string]> = [
  [[1, 20], "水瓶座"],
  [[2, 19], "双鱼座"],
  [[3, 21], "白羊座"],
  [[4, 20], "金牛座"],
  [[5, 21], "双子座"],
  [[6, 22], "巨蟹座"],
  [[7, 23], "狮子座"],
  [[8, 23], "处女座"],
  [[9, 23], "天秤座"],
  [[10, 24], "天蝎座"],
  [[11, 23], "射手座"],
  [[12, 22], "摩羯座"],
];

export const zodiacOptions = ZODIAC_RANGES.map(([, name]) => name);

export function calculateZodiac(birthDate: string): string {
  if (!birthDate) {
    return "";
  }

  const [, monthValue, dayValue] = birthDate.split("-").map(Number);
  const monthDay: [number, number] = [monthValue, dayValue];
  let zodiac = "摩羯座";

  for (const [start, name] of ZODIAC_RANGES) {
    if (isAfterOrSame(monthDay, start)) {
      zodiac = name;
    } else {
      break;
    }
  }

  return zodiac;
}

function isAfterOrSame(left: [number, number], right: [number, number]): boolean {
  return left[0] > right[0] || (left[0] === right[0] && left[1] >= right[1]);
}
