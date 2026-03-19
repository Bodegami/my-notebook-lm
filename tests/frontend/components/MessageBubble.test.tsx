/**
 * MessageBubble component tests.
 * Run from frontend/ directory: npx jest tests/frontend/components/MessageBubble.test.tsx
 * Requires: npm install --save-dev jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom @types/jest ts-jest
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { MessageBubble } from "../../../frontend/src/components/MessageBubble";
import type { ChatMessage } from "../../../frontend/src/types/chat";

const makeUserMessage = (content: string): ChatMessage => ({
  id: "user-1",
  role: "user",
  content,
  citations: [],
  timestamp: new Date(),
});

const makeAssistantMessage = (content: string, citations = []): ChatMessage => ({
  id: "assistant-1",
  role: "assistant",
  content,
  citations,
  timestamp: new Date(),
});

describe("MessageBubble", () => {
  it("renders user message with right alignment class", () => {
    const { container } = render(<MessageBubble message={makeUserMessage("Hello")} />);
    expect(container.querySelector(".justify-end")).toBeTruthy();
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("renders assistant message with left alignment class", () => {
    const { container } = render(<MessageBubble message={makeAssistantMessage("Hi there")} />);
    expect(container.querySelector(".justify-start")).toBeTruthy();
    expect(screen.getByText(/Hi there/i)).toBeInTheDocument();
  });

  it("renders streaming cursor when isStreaming is true", () => {
    const streamingMsg: ChatMessage = {
      ...makeAssistantMessage("Thinking..."),
      isStreaming: true,
    };
    const { container } = render(<MessageBubble message={streamingMsg} />);
    expect(container.querySelector(".animate-blink")).toBeTruthy();
  });

  it("does not render streaming cursor when not streaming", () => {
    const { container } = render(<MessageBubble message={makeAssistantMessage("Done.")} />);
    expect(container.querySelector(".animate-blink")).toBeNull();
  });

  it("renders SourcesPanel when citations are present", () => {
    const citation = {
      id: 1,
      source_filename: "book.pdf",
      page_number: 42,
      section_heading: null,
      excerpt: "Some excerpt text",
    };
    const msg = makeAssistantMessage("Answer [1]", [citation]);
    render(<MessageBubble message={msg} />);
    expect(screen.getByText(/Sources Consulted/)).toBeInTheDocument();
  });

  it("does not render SourcesPanel when no citations", () => {
    render(<MessageBubble message={makeAssistantMessage("No sources")} />);
    expect(screen.queryByText(/Sources Consulted/)).toBeNull();
  });
});
