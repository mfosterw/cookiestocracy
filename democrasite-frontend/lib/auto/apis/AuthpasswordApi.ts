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
  PasswordChange,
  PasswordReset,
  PasswordResetConfirm,
  RestAuthDetail,
} from '../models/index';
import {
    PasswordChangeFromJSON,
    PasswordChangeToJSON,
    PasswordResetFromJSON,
    PasswordResetToJSON,
    PasswordResetConfirmFromJSON,
    PasswordResetConfirmToJSON,
    RestAuthDetailFromJSON,
    RestAuthDetailToJSON,
} from '../models/index';

export interface AuthpasswordChangeCreateRequest {
    passwordChange: PasswordChange;
}

export interface AuthpasswordResetConfirmCreateRequest {
    passwordResetConfirm: PasswordResetConfirm;
}

export interface AuthpasswordResetCreateRequest {
    passwordReset: PasswordReset;
}

/**
 *
 */
export class AuthpasswordApi extends runtime.BaseAPI {

    /**
     * Calls Django Auth SetPasswordForm save method.  Accepts the following POST parameters: new_password1, new_password2 Returns the success/fail message.
     */
    async authpasswordChangeCreateRaw(requestParameters: AuthpasswordChangeCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<RestAuthDetail>> {
        if (requestParameters.passwordChange === null || requestParameters.passwordChange === undefined) {
            throw new runtime.RequiredError('passwordChange','Required parameter requestParameters.passwordChange was null or undefined when calling authpasswordChangeCreate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        const response = await this.request({
            path: `/api/authpassword/change/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: PasswordChangeToJSON(requestParameters.passwordChange),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => RestAuthDetailFromJSON(jsonValue));
    }

    /**
     * Calls Django Auth SetPasswordForm save method.  Accepts the following POST parameters: new_password1, new_password2 Returns the success/fail message.
     */
    async authpasswordChangeCreate(requestParameters: AuthpasswordChangeCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<RestAuthDetail> {
        const response = await this.authpasswordChangeCreateRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Password reset e-mail link is confirmed, therefore this resets the user\'s password.  Accepts the following POST parameters: token, uid,     new_password1, new_password2 Returns the success/fail message.
     */
    async authpasswordResetConfirmCreateRaw(requestParameters: AuthpasswordResetConfirmCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<RestAuthDetail>> {
        if (requestParameters.passwordResetConfirm === null || requestParameters.passwordResetConfirm === undefined) {
            throw new runtime.RequiredError('passwordResetConfirm','Required parameter requestParameters.passwordResetConfirm was null or undefined when calling authpasswordResetConfirmCreate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        const response = await this.request({
            path: `/api/authpassword/reset/confirm/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: PasswordResetConfirmToJSON(requestParameters.passwordResetConfirm),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => RestAuthDetailFromJSON(jsonValue));
    }

    /**
     * Password reset e-mail link is confirmed, therefore this resets the user\'s password.  Accepts the following POST parameters: token, uid,     new_password1, new_password2 Returns the success/fail message.
     */
    async authpasswordResetConfirmCreate(requestParameters: AuthpasswordResetConfirmCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<RestAuthDetail> {
        const response = await this.authpasswordResetConfirmCreateRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Calls Django Auth PasswordResetForm save method.  Accepts the following POST parameters: email Returns the success/fail message.
     */
    async authpasswordResetCreateRaw(requestParameters: AuthpasswordResetCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<runtime.ApiResponse<RestAuthDetail>> {
        if (requestParameters.passwordReset === null || requestParameters.passwordReset === undefined) {
            throw new runtime.RequiredError('passwordReset','Required parameter requestParameters.passwordReset was null or undefined when calling authpasswordResetCreate.');
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters['Content-Type'] = 'application/json';

        if (this.configuration && this.configuration.apiKey) {
            headerParameters["Authorization"] = await this.configuration.apiKey("Authorization"); // tokenAuth authentication
        }

        const response = await this.request({
            path: `/api/authpassword/reset/`,
            method: 'POST',
            headers: headerParameters,
            query: queryParameters,
            body: PasswordResetToJSON(requestParameters.passwordReset),
        }, initOverrides);

        return new runtime.JSONApiResponse(response, (jsonValue) => RestAuthDetailFromJSON(jsonValue));
    }

    /**
     * Calls Django Auth PasswordResetForm save method.  Accepts the following POST parameters: email Returns the success/fail message.
     */
    async authpasswordResetCreate(requestParameters: AuthpasswordResetCreateRequest, initOverrides?: RequestInit | runtime.InitOverrideFunction): Promise<RestAuthDetail> {
        const response = await this.authpasswordResetCreateRaw(requestParameters, initOverrides);
        return await response.value();
    }

}