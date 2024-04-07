import type {
  GetServerSidePropsContext,
  NextApiRequest,
  NextApiResponse,
} from "next";
import { type NextAuthOptions, getServerSession } from "next-auth";
import GithubProvider from "next-auth/providers/github";
import { authApi } from "@/lib";

// You'll need to import and pass this to `NextAuth` in `app/api/auth/[...nextauth]/route.ts`
export const authOptions = {
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
        user.access_key = token.key;

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
} satisfies NextAuthOptions;

// In the next version this will be returned by NextAuth(), which will be called here,
export function auth(
  ...args:
    | [GetServerSidePropsContext["req"], GetServerSidePropsContext["res"]]
    | [NextApiRequest, NextApiResponse]
    | []
) {
  return getServerSession(...args, authOptions);
}
