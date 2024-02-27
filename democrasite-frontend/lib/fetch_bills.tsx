export default function fetchBills() {
  return fetch(`${process.env.BASE_API_URL}/bills/`, {
    next: { revalidate: 60 }, // revalidate every minute for testing
  }).then((response) => response.json());
}

export function fetchBill(id: number) {
  return fetch(`${process.env.BASE_API_URL}/bills/${id}`, {
    cache: "no-store", // no caching for testing (probably want to cache info but not vote data)
  }).then((response) => response.json());
}
