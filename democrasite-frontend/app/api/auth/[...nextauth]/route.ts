import { authApi } from "@/lib";
import { NextAuthOptions } from "next-auth";
import NextAuth from "next-auth/next";
import GithubProvider from "next-auth/providers/github";

export const authOptions: NextAuthOptions = {
  providers: [
    GithubProvider({
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_SECRET!,
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
    async jwt({ token, user }) {
      if (user) {
        token.access_key = user.access_key;
      }

      return token;
    },

    async session({ session, token }) {
      session.user.access_key = token.access_key;

      return session;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
