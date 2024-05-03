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

import { exists, mapValues } from '../runtime';
/**
 *
 * @export
 * @interface SocialLoginRequest
 */
export interface SocialLoginRequest {
    /**
     *
     * @type {string}
     * @memberof SocialLoginRequest
     */
    accessToken?: string;
    /**
     *
     * @type {string}
     * @memberof SocialLoginRequest
     */
    code?: string;
    /**
     *
     * @type {string}
     * @memberof SocialLoginRequest
     */
    idToken?: string;
}

/**
 * Check if a given object implements the SocialLoginRequest interface.
 */
export function instanceOfSocialLoginRequest(value: object): boolean {
    let isInstance = true;

    return isInstance;
}

export function SocialLoginRequestFromJSON(json: any): SocialLoginRequest {
    return SocialLoginRequestFromJSONTyped(json, false);
}

export function SocialLoginRequestFromJSONTyped(json: any, ignoreDiscriminator: boolean): SocialLoginRequest {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {

        'accessToken': !exists(json, 'access_token') ? undefined : json['access_token'],
        'code': !exists(json, 'code') ? undefined : json['code'],
        'idToken': !exists(json, 'id_token') ? undefined : json['id_token'],
    };
}

export function SocialLoginRequestToJSON(value?: SocialLoginRequest | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {

        'access_token': value.accessToken,
        'code': value.code,
        'id_token': value.idToken,
    };
}