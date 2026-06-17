import { MessageSquare } from "lucide-react";

export function FloatingChatButton() {
  return (
    <a
      href="mailto:suporte@merakia.com"
      aria-label="Suporte por email"
      className="fixed bottom-6 right-6 z-20 w-14 h-14 rounded-full bg-brand-500 hover:bg-brand-600
                 text-white flex items-center justify-center shadow-glow transition-all"
    >
      <MessageSquare className="w-6 h-6" />
    </a>
  );
}
