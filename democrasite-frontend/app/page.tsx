import { BillsApi } from "@/api/auto";
import BillList from "@/components/BillList/BillList";

const api = new BillsApi();

export default async function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <BillList bill_list={await api.billsList()} />
    </main>
  );
}
