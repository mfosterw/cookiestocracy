import NextAuth from "next-auth";
import GithubProvider from "next-auth/providers/github";
import { decodeJwt } from "jose";
import { authApi, tokenApi } from "@/lib/api";
import "next-auth/jwt";
import { JWT } from "next-auth/jwt";

async function refreshAccessToken(token: JWT) {
  try {
    if (!token.refresh_token) {
      return;
    }

    const tokens = await tokenApi.tokenRefreshCreate({
      tokenRefreshRequest: { refresh: token.refresh_token },
    });

    const { exp } = decodeJwt(tokens.access);

    return {
      ...token,
      access_token: tokens.access,
      expires_at: exp,
      // refresh_token: tokens.refresh || token.refresh_token, // If token rotation is enabled
    } as JWT;
  } catch (error) {
    console.error("Error refreshing access token.", error?.toString());
  }
}

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
          socialLoginRequest: { accessToken: account.access_token },
        });

        user.access_token = token.access;
        user.refresh_token = token.refresh;

        return true;
      }

      return false; // Unreachable
    },

    async jwt({ token, user, account }) {
      // eslint thinks user is always defined but it is not
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
      if (account && user) {
        const { exp } = decodeJwt(user.access_token);

        return {
          access_token: user.access_token,
          expires_at: exp,
          refresh_token: user.refresh_token,
        } as JWT;
      }

      // TODO: This doesn't seem to always catch server actions using expired tokens
      if (token.expires_at && Date.now() < token.expires_at * 1000) {
        return token;
      }

      console.debug("Token expired, refreshing");
      // Refresh the token or end session by returning null
      return (await refreshAccessToken(token)) || null;
    },

    session({ session, token }) {
      // I would prefer to keep this server-side only but currently that is impractical
      session.access_token = token.access_token as string;

      return session;
    },
  },

  events: {
    async signOut(message) {
      if ("token" in message) {
        const jwt = await message.token;
        if (jwt?.refresh_token) {
          await authApi.authLogoutCreate({
            tokenRefreshRequest: { refresh: jwt.refresh_token },
          });
        }
      }
    },
  },
});

declare module "next-auth" {
  interface Session {
    /** The user's API access token */
    access_token: string;
  }

  interface User {
    access_token: string;
    refresh_token: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    refresh_token?: string;
    expires_at?: number;
  }
}
