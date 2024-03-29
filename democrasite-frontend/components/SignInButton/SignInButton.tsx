"use client";

import { Button } from "@mantine/core";
import { signIn } from "next-auth/react";

export function SignInButton() {
  return (
    <Button onClick={() => signIn()} mb={20}>
      Sign in
    </Button>
  );
}
