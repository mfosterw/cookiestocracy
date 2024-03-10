import {
  AuthApi,
  BillsApi,
  Configuration,
  ConfigurationParameters,
  ResponseContext,
  UsersApi,
} from "./auto";

class Api {
  protected params: ConfigurationParameters;
  config: Configuration;
  authApi: AuthApi = new AuthApi();
  billsApi: BillsApi = new BillsApi();
  usersApi: UsersApi = new UsersApi();

  constructor() {
    this.params = {
      basePath: process.env.BASE_API_URL,
      // TODO: credentials: "include" is not working
      // (see also django-cors settings, which did not immediately fix the issue but are probably necessary)
      credentials: "include",
      middleware: [{ post: this.propogateSessionMiddleWare.bind(this) }],
    };
    this.config = new Configuration(this.params);

    this.authApi = new AuthApi(this.config);
    this.billsApi = new BillsApi(this.config);
    this.usersApi = new UsersApi(this.config);
  }

  setCookie(cookie: string) {
    this.params.headers = {
      ...this.params.headers,
      Cookie: cookie,
    };
    this.config.config = new Configuration(this.params);
  }

  async propogateSessionMiddleWare({
    url,
    response,
  }: ResponseContext): Promise<Response> {
    if (
      response.headers.get("set-cookie") === null ||
      !/\/api\/auth\/.*/.test(url)
    ) {
      return response;
    }

    response.headers.getSetCookie().forEach((cookie) => {
      if (cookie.startsWith("sessionid")) {
        this.setCookie(cookie);
      }
    });

    return response;
  }
}

const api = new Api();
export default api;
