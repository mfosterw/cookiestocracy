import NextAuth from "next-auth/next";
import { authOptions } from "@/auth";

// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
const handler = NextAuth(authOptions);
// The next version of NextAuth has a better way to export this
export { handler as GET, handler as POST };
