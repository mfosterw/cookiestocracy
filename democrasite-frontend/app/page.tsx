import BillList from "@/components/BillList/BillList";
import fetchBills from "@/lib/fetch_bills";

export default async function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <BillList bill_list={await fetchBills()} />
    </main>
  );
}
