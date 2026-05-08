import { calculateZodiac } from "../src/lib/zodiac";

describe("calculateZodiac", () => {
  it("根据出生年月日计算星座", () => {
    expect(calculateZodiac("1995-08-18")).toBe("狮子座");
    expect(calculateZodiac("1995-12-22")).toBe("摩羯座");
    expect(calculateZodiac("1995-01-19")).toBe("摩羯座");
    expect(calculateZodiac("1995-01-20")).toBe("水瓶座");
  });
});
