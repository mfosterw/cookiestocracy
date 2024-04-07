import { auth } from "@/auth";

import { Configuration, AuthApi, BillsApi, UsersApi } from "./auto";

const config = new Configuration({
  basePath: process.env.BASE_API_URL,
  // The access key is not technically an API key but it is labeled that way by the schema generator
  apiKey: async () => {
    try {
      const session = await auth();

      if (session) {
        // see https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
        return `Token ${session.user.access_key}`;
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
