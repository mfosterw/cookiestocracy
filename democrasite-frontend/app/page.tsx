import { billsApi } from "@/lib";
import { BillList, SignInButton, SignOutButton } from "@/components";
import { getServerSession } from "next-auth";
import { authOptions } from "./api/auth/[...nextauth]/route";

export default async function Home() {
  const session = await getServerSession(authOptions);

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      {session === null ? (
        <SignInButton provider="github" />
      ) : (
        <SignOutButton />
      )}
      <BillList bill_list={await billsApi.billsList()} />
    </main>
  );
}
