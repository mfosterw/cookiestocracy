import { Button } from "@mantine/core";

export function SignInButton() {
  return (
    <form action="/api/auth/github" method="post">
      <Button type="submit" mb={20}>
        Sign in with GitHub
      </Button>
    </form>
  );
}
