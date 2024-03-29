import { getServerSession } from "next-auth";
import { Configuration, AuthApi, BillsApi, UsersApi, VoteApi } from "./auto";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

const config = new Configuration({
  basePath: process.env.BASE_API_URL,
  // The access key is not technically an API key but it is labeled that way by the schema generator
  apiKey: async () => {
    try {
      const session = await getServerSession(authOptions);

      if (session) {
        // see https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
        return `Token ${session?.user?.access_key}`;
      }
    } catch (error) {
      // e.g. when running getStaticProps
    }

    return "";
  },
});

export const authApi = new AuthApi(config);
export const billsApi = new BillsApi(config);
export const usersApi = new UsersApi(config);
export const voteApi = new VoteApi(config);
