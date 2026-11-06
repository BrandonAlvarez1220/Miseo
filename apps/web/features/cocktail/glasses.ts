/**
 * SVG geometry for each glass, in a 240×300 box. Liquid is drawn as stacked
 * rectangles clipped by `interior`, so it automatically takes the glass shape.
 */

export interface GlassShape {
  /** Inside of the glass (clip path for liquid, ice and bubbles). */
  interior: string;
  /** Visible outline of the bowl/body. */
  outline: string;
  /** Extra strokes: stem, base, handle... */
  details: string[];
  /** Y of the bottom of the liquid and of a "full" drink. */
  bottom: number;
  fullTop: number;
  /** Rim: y and x-range, used to place garnish. */
  rimY: number;
  rimLeft: number;
  rimRight: number;
  /** Horizontal range where ice cubes sit. */
  iceLeft: number;
  iceRight: number;
  /** Opaque body tint (copper mug, tiki ceramic). */
  bodyFill?: string;
}

const stemAndBase = (from: number) => [
  `M120 ${from} L120 238`,
  "M78 246 Q120 234 162 246 Q120 254 78 246 Z",
];

export const GLASSES: Record<string, GlassShape> = {
  rocks: {
    interior: "M70 140 L170 140 L166 236 Q165 244 157 244 L83 244 Q75 244 74 236 Z",
    outline: "M66 130 L174 130 L169 244 Q168 256 156 256 L84 256 Q72 256 71 244 Z",
    details: [],
    bottom: 244,
    fullTop: 158,
    rimY: 130,
    rimLeft: 66,
    rimRight: 174,
    iceLeft: 78,
    iceRight: 162,
  },
  highball: {
    interior: "M84 62 L156 62 L154 238 Q154 244 148 244 L92 244 Q86 244 86 238 Z",
    outline: "M80 52 L160 52 L158 244 Q157 256 146 256 L94 256 Q83 256 82 244 Z",
    details: [],
    bottom: 244,
    fullTop: 80,
    rimY: 52,
    rimLeft: 80,
    rimRight: 160,
    iceLeft: 90,
    iceRight: 150,
  },
  collins: {
    interior: "M90 50 L150 50 L149 238 Q149 244 143 244 L97 244 Q91 244 91 238 Z",
    outline: "M86 40 L154 40 L153 244 Q152 256 141 256 L99 256 Q88 256 87 244 Z",
    details: [],
    bottom: 244,
    fullTop: 70,
    rimY: 40,
    rimLeft: 86,
    rimRight: 154,
    iceLeft: 96,
    iceRight: 144,
  },
  coupe: {
    interior: "M52 104 Q54 160 120 162 Q186 160 188 104 Z",
    outline: "M46 98 Q48 168 120 168 Q192 168 194 98",
    details: stemAndBase(168),
    bottom: 162,
    fullTop: 110,
    rimY: 98,
    rimLeft: 46,
    rimRight: 194,
    iceLeft: 90,
    iceRight: 150,
  },
  martini: {
    interior: "M52 90 L120 158 L188 90 Z",
    outline: "M44 82 L120 164 L196 82",
    details: stemAndBase(164),
    bottom: 158,
    fullTop: 96,
    rimY: 82,
    rimLeft: 44,
    rimRight: 196,
    iceLeft: 100,
    iceRight: 140,
  },
  "nick-and-nora": {
    interior: "M70 100 Q68 152 120 160 Q172 152 170 100 Z",
    outline: "M64 92 Q62 162 120 166 Q178 162 176 92",
    details: stemAndBase(166),
    bottom: 160,
    fullTop: 108,
    rimY: 92,
    rimLeft: 64,
    rimRight: 176,
    iceLeft: 96,
    iceRight: 144,
  },
  "copa-de-vino": {
    interior: "M76 76 Q62 150 120 166 Q178 150 164 76 Z",
    outline: "M72 64 Q54 156 120 172 Q186 156 168 64",
    details: stemAndBase(172),
    bottom: 166,
    fullTop: 104,
    rimY: 64,
    rimLeft: 72,
    rimRight: 168,
    iceLeft: 92,
    iceRight: 148,
  },
  flauta: {
    interior: "M101 52 Q96 150 120 168 Q144 150 139 52 Z",
    outline: "M97 44 Q90 156 120 174 Q150 156 143 44",
    details: stemAndBase(174),
    bottom: 168,
    fullTop: 66,
    rimY: 44,
    rimLeft: 97,
    rimRight: 143,
    iceLeft: 108,
    iceRight: 132,
  },
  "taza-de-cobre": {
    interior: "M66 116 L174 116 L170 238 Q170 246 162 246 L78 246 Q70 246 70 238 Z",
    outline: "M62 108 L178 108 L174 246 Q173 256 162 256 L78 256 Q67 256 66 246 Z",
    details: ["M177 140 Q216 144 212 182 Q208 214 173 212"],
    bottom: 246,
    fullTop: 130,
    rimY: 108,
    rimLeft: 62,
    rimRight: 178,
    iceLeft: 76,
    iceRight: 164,
    bodyFill: "#c0703a",
  },
  tiki: {
    interior: "M82 72 L158 72 L155 240 L85 240 Z",
    outline: "M78 62 L162 62 L159 250 L81 250 Z",
    details: ["M96 120 h16 M128 120 h16 M104 150 h32", "M100 176 Q120 192 140 176"],
    bottom: 240,
    fullTop: 88,
    rimY: 62,
    rimLeft: 78,
    rimRight: 162,
    iceLeft: 90,
    iceRight: 150,
    bodyFill: "#8a5a3c",
  },
};

export function glassShape(slug: string): GlassShape {
  return GLASSES[slug] ?? GLASSES.rocks;
}

/** Mixing vessels, drawn to the left of the glass. Same coordinate conventions. */
export const VESSELS = {
  shaker: {
    interior: "M70 120 L150 120 L144 250 L76 250 Z",
    outline: "M64 110 L156 110 L149 256 L71 256 Z",
    cap: "M74 62 L146 62 L156 110 L64 110 Z",
    bottom: 250,
    fullTop: 150,
  },
  "mixing-glass": {
    interior: "M74 110 L146 110 L144 248 L76 248 Z",
    outline: "M66 100 L154 100 L150 256 L70 256 Z M154 100 L166 94",
    cap: null,
    bottom: 248,
    fullTop: 150,
  },
} as const;
