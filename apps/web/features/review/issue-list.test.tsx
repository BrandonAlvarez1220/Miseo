import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IssueList, issueTitle } from "./issue-list";

describe("IssueList", () => {
  it("shows a Spanish title per code and keeps the API message as detail", () => {
    render(
      <IssueList
        issues={[
          {
            severity: "error",
            code: "unknown_ingredient",
            message: "'x' is not in the catalog",
            field_path: null,
          },
          { severity: "info", code: "brand_new_code", message: "something", field_path: null },
        ]}
      />,
    );

    expect(screen.getByText("Ingrediente que el catálogo no conoce")).toBeInTheDocument();
    expect(screen.getByText("'x' is not in the catalog")).toBeInTheDocument();
    // An unknown code falls back to the code itself instead of hiding the issue.
    expect(screen.getByText("brand_new_code")).toBeInTheDocument();
  });

  it("says so when there is nothing to report", () => {
    render(<IssueList issues={[]} />);
    expect(screen.getByText("Sin problemas detectados.")).toBeInTheDocument();
  });

  it("covers every issue code the API can produce", () => {
    for (const code of [
      "unknown_ingredient",
      "unknown_unit",
      "possible_duplicate",
      "license_unknown",
    ]) {
      expect(issueTitle(code)).not.toBe(code);
    }
  });
});
