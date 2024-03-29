import { billsApi } from "@/lib";
import { BillList, SignInButton } from "@/components";

export default async function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <SignInButton />
      <BillList bill_list={await billsApi.billsList()} />
    </main>
  );
}
