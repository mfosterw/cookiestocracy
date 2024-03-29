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
 * @interface SocialLogin
 */
export interface SocialLogin {
    /**
     *
     * @type {string}
     * @memberof SocialLogin
     */
    accessToken?: string;
    /**
     *
     * @type {string}
     * @memberof SocialLogin
     */
    code?: string;
    /**
     *
     * @type {string}
     * @memberof SocialLogin
     */
    idToken?: string;
}

/**
 * Check if a given object implements the SocialLogin interface.
 */
export function instanceOfSocialLogin(value: object): boolean {
    let isInstance = true;

    return isInstance;
}

export function SocialLoginFromJSON(json: any): SocialLogin {
    return SocialLoginFromJSONTyped(json, false);
}

export function SocialLoginFromJSONTyped(json: any, ignoreDiscriminator: boolean): SocialLogin {
    if ((json === undefined) || (json === null)) {
        return json;
    }
    return {

        'accessToken': !exists(json, 'access_token') ? undefined : json['access_token'],
        'code': !exists(json, 'code') ? undefined : json['code'],
        'idToken': !exists(json, 'id_token') ? undefined : json['id_token'],
    };
}

export function SocialLoginToJSON(value?: SocialLogin | null): any {
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
