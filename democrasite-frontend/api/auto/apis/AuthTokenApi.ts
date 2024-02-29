/* tslint:disable */
/* eslint-disable */
/**
 * Democrasite API
 * Documentation of API endpoints of Democrasite
 *
 * The version of the OpenAPI document: 1.0.0
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */


import * as runtime from '../runtime';
import type {
  AuthToken,
} from '../models/index';
import {
    AuthTokenFromJSON,
    AuthTokenToJSON,
} from '../models/index';

export interface AuthTokenCreateRequest {
    username: string;
    password: string;
    token: string;
}

/**
 *
 */
export class AuthTokenApi extends runtime.BaseAPI {

    /**
     */
    async authTokenCreateRaw(requestParameters: AuthTokenCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<AuthToken>> {
        if (requestParameters.username === null || requestParameters.username === undefined) {
            throw new runtime.RequiredError('username','Required parameter requestParameters.username was null or undefined when calling authTokenCreate.');
        }

        if (requestParameters.password === null || requestParameters.password === undefined) {
            throw new runtime.RequiredError('password','Required parameter requestParameters.password was null or undefined when calling authTokenCreate.');
        }

        if (requestParameters.token === null || requestParameters.token === undefined) {
            throw new runtime.RequiredError('token','Required parameter requestParameters.token was null or undefined when calling authTokenCreate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        const consumes: runtime.Consume[] = [
            { contentType: 'application/x-www-form-urlencoded' },
            { contentType: 'multipart/form-data' },
            { contentType: 'application/json' },
        ];
        // @ts-ignore: canConsumeForm may be unused
        const canConsumeForm = runtime.canConsumeForm(consumes);

        let formParams: { append(param: string, value: any): any };
        let useForm = false;
        if (useForm) {
            formParams = new FormData();
        } else {
            formParams = new URLSearchParams();
        }

        if (requestParameters.username !== undefined) {
            formParams.append('username', requestParameters.username as any);
        }

        if (requestParameters.password !== undefined) {
            formParams.append('password', requestParameters.password as any);
        }

        if (requestParameters.token !== undefined) {
            formParams.append('token', requestParameters.token as any);
        }

        const response = await this.request({
            path: `/auth-token/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: formParams,
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => AuthTokenFromJSON(jsonValue));
    }

    /**
     */
    async authTokenCreate(requestParameters: AuthTokenCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<AuthToken> {
        const response = await this.authTokenCreateRaw(requestParameters, initOverrides);
        return await response.value();
    }

}