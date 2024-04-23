import NextAuth, { DefaultSession } from "next-auth";
import GithubProvider from "next-auth/providers/github";
import { authApi } from "@/lib/api";
import "next-auth/jwt";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_CLIENT_ID || "",
      clientSecret: process.env.GITHUB_SECRET || "",
    }),
  ],

  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "github") {
        const token = await authApi.authGithubCreate({
          socialLogin: { accessToken: account.access_token },
        });

        // I named this access_key to distinguish from an OAuth access_token
        // It is not technically an API key even though the API client calls it one
        user.access_key = token.access;

        return true;
      }

      return false; // Unreachable
    },

    jwt({ token, user }) {
      // TODO: This if statement was included in documentation examples but eslint
      // doesn't like it.
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
      if (user) {
        token.access_key = user.access_key;
      }

      return token;
    },

    session({ session, token }) {
      session.user.access_key = token.access_key;

      return session;
    },
  },

  events: {
    async signOut() {
      await authApi.authLogoutCreate();
    },
  },
});

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

declare module "next-auth/jwt" {
  interface JWT {
    access_key: string;
  }
}
