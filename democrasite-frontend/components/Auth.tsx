"use client";

import { Button } from "@mantine/core";
import { BuiltInProviderType } from "next-auth/providers/index";
import { signIn, signOut } from "next-auth/react";

export function SignInButton({ provider }: { provider: BuiltInProviderType }) {
  return (
    <Button onClick={() => signIn(provider)} mb={20}>
      Login with {provider.charAt(0).toUpperCase() + provider.slice(1)}
    </Button>
  );
}

export function SignOutButton() {
  return (
    <Button onClick={() => signOut()} mb={20}>
      Log out
    </Button>
  );
}
