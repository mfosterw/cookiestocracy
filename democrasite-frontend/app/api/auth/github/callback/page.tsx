export async function getServerSideProps({
  searchParams,
}: {
  searchParams: any;
}) {
  await fetch(
    "http://localhost:3000/api/auth/github?" +
      new URLSearchParams(searchParams).toString()
  );
}
