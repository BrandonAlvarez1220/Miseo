/**
 * Only same-site relative paths are valid post-login destinations; anything else
 * (absolute URLs, protocol-relative `//evil.com`, backslash tricks) falls back to "/".
 * Prevents open-redirect abuse of the `next` parameter.
 */
export function safeRedirectPath(value: string | null | undefined, fallback = "/"): string {
  if (!value || !value.startsWith("/")) return fallback;
  if (value.startsWith("//") || value.includes("\\")) return fallback;
  // Control characters (e.g. newlines) can smuggle a second header or URL.
  if ([...value].some((char) => char.charCodeAt(0) < 0x20 || char.charCodeAt(0) === 0x7f)) {
    return fallback;
  }
  return value;
}
