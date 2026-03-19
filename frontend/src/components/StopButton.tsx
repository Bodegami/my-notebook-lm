"use client";

import { Square } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StopButtonProps {
  onClick: () => void;
}

export function StopButton({ onClick }: StopButtonProps) {
  return (
    <Button
      variant="destructive"
      size="sm"
      onClick={onClick}
      className="gap-1.5"
    >
      <Square className="h-3.5 w-3.5 fill-current" />
      Stop
    </Button>
  );
}
