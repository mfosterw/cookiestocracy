"use server";

import { cookies } from "next/headers";
import crypto from "crypto";
import { redirect } from "next/navigation";
import api from "@/lib/api";
import { NextRequest } from "next/server";
import { revalidatePath } from "next/cache";

export async function POST() {
  // Length was chosen randomly
  const state = crypto.randomBytes(32).toString("hex");
  cookies().set("github-oauth-state", state, {
    sameSite: "lax",
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
  });

  redirect(
    `https://github.com/login/oauth/authorize?client_id=${process.env.GITHUB_CLIENT_ID}&state=${state}&scope=user:email`
  );
}

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  const serverState = cookies().get("github-oauth-state");
  cookies().delete("github-oauth-state");

  if (!code || !state || state !== serverState!.value) {
    return redirect("/");
  }

  const token = await api.authApi.authGithubCreate({
    socialLogin: { code: code },
  });

  await revalidatePath("/", "layout");

  redirect("/");
}
