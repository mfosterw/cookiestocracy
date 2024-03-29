import NextAuth from "next-auth";

declare module "next-auth" {
  /**
   * Returned by `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    user: {
      /** The user's API access token */
      access_key: string;
    } & DefaultSession["user"];
  }
  interface User {
    access_key: string;
  }
}
