"use client";

import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

export function useSession() {
  const [sessionId, setSessionId] = useState<string>("");

  useEffect(() => {
    let id = sessionStorage.getItem("sessionId");
    if (!id) {
      id = uuidv4();
      sessionStorage.setItem("sessionId", id);
    }
    setSessionId(id);
  }, []);

  return { sessionId };
}
