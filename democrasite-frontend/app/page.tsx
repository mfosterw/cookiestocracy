import api from "@/lib/api";
import { BillList } from "@/components";
import { SignInButton } from "@/components";
import { cookies } from "next/headers";

export default async function Home() {
  // console.log(cookies().getAll());
  // console.log(await api.billsApi.billsList());
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <SignInButton />
      <BillList bill_list={await api.billsApi.billsList()} />
    </main>
  );
}
