"use client";

import { useEffect, useRef } from "react";

/**
 * Progressive enhancement for GET filter forms:
 * - submits the surrounding form whenever one of its selects changes;
 * - drops empty fields so URLs stay clean (`?tipo=drink`, not `?tipo=drink&categoria=`).
 * Without JavaScript the form's submit button still works.
 */
export function AutoSubmit() {
  const marker = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const form = marker.current?.closest("form");
    if (!form) return;
    const onChange = (event: Event) => {
      if (event.target instanceof HTMLSelectElement) form.requestSubmit();
    };
    const onFormData = (event: FormDataEvent) => {
      for (const [key, value] of [...event.formData.entries()]) {
        if (value === "") event.formData.delete(key);
      }
    };
    form.addEventListener("change", onChange);
    form.addEventListener("formdata", onFormData);
    return () => {
      form.removeEventListener("change", onChange);
      form.removeEventListener("formdata", onFormData);
    };
  }, []);

  return <span ref={marker} hidden />;
}
