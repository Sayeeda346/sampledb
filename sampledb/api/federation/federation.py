# coding: utf-8
"""
RESTful API for SampleDB
"""

import datetime
import flask

from flask_restful import Resource

from ...logic import errors
from ...logic.shares import get_shares_for_component
from ...logic.federation import import_updates, shared_action_preprocessor, shared_user_preprocessor, shared_instrument_preprocessor, shared_location_preprocessor, shared_object_preprocessor, shared_action_type_preprocessor, PROTOCOL_VERSION_MAJOR, PROTOCOL_VERSION_MINOR
from ...api.federation.authentication import http_token_auth


def share_to_json(share):
    return {
        'object_id': share.object_id,
        'policy': share.policy,
        'utc_datetime': share.utc_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')
    }


class UpdateHook(Resource):
    @http_token_auth.login_required
    def post(self):
        try:
            import_updates(flask.g.component)
        except errors.UnauthorizedRequestError:
            pass
        except errors.NoAuthenticationMethodError:
            pass
        except errors.InvalidDataExportError:
            pass
        except errors.MissingComponentAddressError:
            pass
        except errors.ComponentNotConfiguredForFederationError:
            pass
        except errors.RequestServerError:
            pass
        except ConnectionError:
            pass


class Objects(Resource):
    @http_token_auth.login_required
    def get(self):
        component = flask.g.component
        shares = get_shares_for_component(component.id)

        result = {
            'header': {
                'db_uuid': flask.current_app.config['FEDERATION_UUID'],
                'target_uuid': component.uuid,
                'protocol_version': {
                    'major': PROTOCOL_VERSION_MAJOR,
                    'minor': PROTOCOL_VERSION_MINOR
                },
                'sync_timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
            }, 'actions': [], 'users': [], 'instruments': [], 'locations': [], 'objects': [], 'action_types': [], 'markdown_images': {}
        }
        refs = []
        markdown_images = {}
        ref_ids = {'actions': [], 'users': [], 'instruments': [], 'locations': [], 'action_types': []}
        preprocessors = {
            'actions': shared_action_preprocessor,
            'users': shared_user_preprocessor,
            'instruments': shared_instrument_preprocessor,
            'locations': shared_location_preprocessor,
            'action_types': shared_action_type_preprocessor
        }

        for share in shares:
            obj = shared_object_preprocessor(share.object_id, share.policy, refs, markdown_images)
            result['objects'].append(obj)

        while len(refs) > 0:
            type, id = refs.pop()
            if type in ref_ids and id not in ref_ids[type]:
                processed = preprocessors[type](id, component, refs, markdown_images)
                if processed is not None:
                    result[type].append(processed)
                ref_ids[type].append(id)

        result['markdown_images'] = markdown_images
        return result