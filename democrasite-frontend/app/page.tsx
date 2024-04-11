import { billsApi } from "@/lib/api";
import { BillList, SignInButton, SignOutButton } from "@/components";
import { auth } from "@/auth";

export default async function Home() {
  const session = await auth();

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
