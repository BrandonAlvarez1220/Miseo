import { ShieldAlert } from "lucide-react";

import { Container } from "@/components/ui/container";
import { StateMessage } from "@/components/ui/state-message";

export function Forbidden({ needs }: { needs: string }) {
  return (
    <Container className="py-16">
      <StateMessage
        tone="danger"
        icon={ShieldAlert}
        title="No tienes permiso para ver esto"
        description={`Esta sección es para ${needs}. Si crees que es un error, pide a un administrador que cambie tu rol.`}
      />
    </Container>
  );
}
