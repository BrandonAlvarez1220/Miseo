"use client";

import { useSyncExternalStore } from "react";

/**
 * "Ya lo cociné" progress, stored only in this browser until accounts exist
 * (Phase 3 will sync it to the user's profile). Every access is wrapped in
 * try/catch: storage can be unavailable (private mode, blocked site data) and the
 * app must keep working without it.
 */

const STORAGE_KEY = "miseo:cooked:v1";
const EMPTY: ReadonlyMap<string, string> = new Map();

type Listener = () => void;
const listeners = new Set<Listener>();
let cache: ReadonlyMap<string, string> | null = null;

function read(): ReadonlyMap<string, string> {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : {};
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return new Map();
    return new Map(
      Object.entries(parsed).filter(
        (entry): entry is [string, string] => typeof entry[1] === "string",
      ),
    );
  } catch {
    return new Map();
  }
}

function snapshot(): ReadonlyMap<string, string> {
  cache ??= read();
  return cache;
}

function write(next: Map<string, string>): void {
  cache = next;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(Object.fromEntries(next)));
  } catch {
    // Not persisted, but the in-memory state still updates for this visit.
  }
  listeners.forEach((listener) => listener());
}

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  // Keep tabs in sync.
  const onStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY) {
      cache = null;
      listener();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

/** Map of recipe slug -> ISO date it was marked as cooked. Empty on the server. */
export function useCookedRecipes(): ReadonlyMap<string, string> {
  return useSyncExternalStore(subscribe, snapshot, () => EMPTY);
}

export function setCooked(slug: string, cooked: boolean): void {
  const next = new Map(snapshot());
  if (cooked) next.set(slug, new Date().toISOString());
  else next.delete(slug);
  write(next);
}

/** Test helper: forget the cached snapshot. */
export function resetProgressCache(): void {
  cache = null;
}
