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
  JWT,
  SocialLoginRequest,
  TokenRefreshRequest,
} from '../models/index';
import {
    JWTFromJSON,
    JWTToJSON,
    SocialLoginRequestFromJSON,
    SocialLoginRequestToJSON,
    TokenRefreshRequestFromJSON,
    TokenRefreshRequestToJSON,
} from '../models/index';

export interface AuthGithubCreateRequest {
    socialLoginRequest?: SocialLoginRequest;
}

export interface AuthLogoutCreateRequest {
    tokenRefreshRequest: TokenRefreshRequest;
}

/**
 *
 */
export class AuthApi extends runtime.BaseAPI {

    /**
     * Login with GitHub using OAuth2
     * Login with GitHub
     */
    async authGithubCreateRaw(requestParameters: AuthGithubCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<JWT>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("jwtAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/auth/github/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: SocialLoginRequestToJSON(requestParameters.socialLoginRequest),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => JWTFromJSON(jsonValue));
    }

    /**
     * Login with GitHub using OAuth2
     * Login with GitHub
     */
    async authGithubCreate(requestParameters: AuthGithubCreateRequest = {}, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<JWT> {
        const response = await this.authGithubCreateRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Logs out the current user and blacklists their refresh token
     * Logout
     */
    async authLogoutCreateRaw(requestParameters: AuthLogoutCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<void>> {
        if (requestParameters.tokenRefreshRequest === null || requestParameters.tokenRefreshRequest === undefined) {
            throw new runtime.RequiredError('tokenRefreshRequest','Required parameter requestParameters.tokenRefreshRequest was null or undefined when calling authLogoutCreate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        if (this.configuration && this.configuration.accessToken) {
            const token = this.configuration.accessToken;
            const tokenString = await token("jwtAuth", []);

            if (tokenString) {
                headerParameters["Authorization"] = `Bearer ${tokenString}`;
            }
        }
        const response = await this.request({
            path: `/api/auth/logout/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: TokenRefreshRequestToJSON(requestParameters.tokenRefreshRequest),
        }, initOverrides);

        return new runtime.VoidApiResponse(response);
    }

    /**
     * Logs out the current user and blacklists their refresh token
     * Logout
     */
    async authLogoutCreate(requestParameters: AuthLogoutCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<void> {
        await this.authLogoutCreateRaw(requestParameters, initOverrides);
    }

}
