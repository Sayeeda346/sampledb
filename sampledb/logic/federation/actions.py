import base64

import flask

from .components import _get_or_create_component_id
from .utils import _get_id, _get_uuid, _get_bool, _get_str, _get_dict
from .action_types import _parse_action_type_ref, _get_or_create_action_type_id
from .instruments import _parse_instrument_ref, _get_or_create_instrument_id
from .users import _parse_user_ref, _get_or_create_user_id
from ..actions import get_action, get_mutable_action, create_action
from ..action_translations import set_action_translation, get_action_translations_for_action
from ..languages import get_languages, get_language, get_language_by_lang_code
from ..instruments import get_instrument
from ..markdown_images import get_markdown_image, find_referenced_markdown_images
from ..components import Component, get_component, get_component_by_uuid
from ..users import get_user
from ..schemas.validate_schema import validate_schema
from .. import errors, fed_logs, markdown_to_html
from ... import db


def parse_action(action_data):
    schema = _get_dict(action_data.get('schema'))
    _parse_schema(schema)
    fed_id = _get_id(action_data.get('action_id'))
    uuid = _get_uuid(action_data.get('component_uuid'))
    if uuid == flask.current_app.config['FEDERATION_UUID']:
        # do not accept updates for own data
        raise errors.InvalidDataExportError('Invalid update for local action {}'.format(fed_id))
    if schema is not None:
        try:
            validate_schema(schema, strict=True)
        except errors.ValidationError as e:
            raise errors.InvalidDataExportError('Invalid schema in action #{} @ {} ({})'.format(fed_id, uuid, e))

    result = {
        'fed_id': fed_id,
        'component_uuid': uuid,
        'action_type': _parse_action_type_ref(_get_dict(action_data.get('action_type'), mandatory=True)),
        'schema': schema,
        'instrument': _parse_instrument_ref(_get_dict(action_data.get('instrument'))),
        'user': _parse_user_ref(_get_dict(action_data.get('user'))),
        'description_is_markdown': _get_bool(action_data.get('description_is_markdown'), default=False),
        'is_hidden': _get_bool(action_data.get('is_hidden'), default=False),
        'short_description_is_markdown': _get_bool(action_data.get('short_description_is_markdown'), default=False),
        'translations': []
    }
    admin_only = _get_bool(action_data.get('admin_only'))
    if admin_only is not None:
        result['admin_only'] = admin_only
    disable_create_objects = _get_bool(action_data.get('disable_create_objects'))
    if disable_create_objects is not None:
        result['disable_create_objects'] = disable_create_objects

    allowed_language_ids = [language.id for language in get_languages(only_enabled_for_input=False)]

    translation_data = _get_dict(action_data.get('translations'))
    if translation_data is not None:
        for lang_code, translation in translation_data.items():
            try:
                language = get_language_by_lang_code(lang_code.lower())
            except errors.LanguageDoesNotExistError:
                continue
            language_id = language.id
            if language_id not in allowed_language_ids:
                continue

            result['translations'].append({
                'language_id': language_id,
                'name': _get_str(translation.get('name')),
                'description': _get_str(translation.get('description')),
                'short_description': _get_str(translation.get('short_description'))
            })
    return result


def import_action(action_data, component):
    def _import_schema(schema, path=[]):
        if schema is None:
            return None
        if schema.get('type') == 'array' and 'items' in schema:
            _import_schema(schema['items'], path + ['[?]'])
        if schema.get('type') == 'object':
            if isinstance(schema.get('properties'), dict):
                for property_name, property_schema in schema['properties'].items():
                    _import_schema(property_schema, path + [property_name])
                    if 'template' in property_schema:
                        try:
                            c = get_component_by_uuid(property_schema['template']['component_uuid'])
                            property_schema['template'] = get_action(property_schema['template']['action_id'], c.id).id
                        except errors.ActionDoesNotExistError:
                            pass
                        except errors.ComponentDoesNotExistError:
                            pass
        return schema

    component_id = _get_or_create_component_id(action_data['component_uuid'])

    action_type_id = _get_or_create_action_type_id(action_data['action_type'])
    instrument_id = _get_or_create_instrument_id(action_data['instrument'])
    user_id = _get_or_create_user_id(action_data['user'])

    schema = _import_schema(action_data['schema'])

    try:
        action = get_mutable_action(action_data['fed_id'], component_id)
        if action.type_id != action_type_id or action.schema != action_data['schema'] or action.instrument_id != instrument_id or action.user_id != user_id or action.description_is_markdown != action_data['description_is_markdown'] or action.is_hidden != action_data['is_hidden'] or action.short_description_is_markdown != action_data['short_description_is_markdown'] or ('admin_only' in action_data and action.admin_only != action_data['admin_only']) or ('disable_create_objects' in action_data and action.disable_create_objects != action_data['disable_create_objects']):
            action.action_type_id = action_type_id
            action.schema = schema
            action.instrument_id = instrument_id
            action.user_id = user_id
            action.description_is_markdown = action_data['description_is_markdown']
            action.is_hidden = action_data['is_hidden']
            action.short_description_is_markdown = action_data['short_description_is_markdown']
            if 'admin_only' in action_data:
                action.admin_only = action_data['admin_only']
            if 'disable_create_objects' in action_data:
                action.disable_create_objects = action_data['disable_create_objects']
            db.session.commit()
            fed_logs.update_action(action.id, component.id)
    except errors.ActionDoesNotExistError:
        action = create_action(
            fed_id=action_data['fed_id'],
            component_id=component_id,
            action_type_id=action_type_id,
            schema=schema,
            instrument_id=instrument_id,
            user_id=user_id,
            description_is_markdown=action_data['description_is_markdown'],
            is_hidden=action_data['is_hidden'],
            short_description_is_markdown=action_data['short_description_is_markdown'],
            admin_only=action_data.get('admin_only', False),
            disable_create_objects=action_data.get('disable_create_objects', False),
        )
        fed_logs.import_action(action.id, component.id)

    for action_translation in action_data['translations']:
        set_action_translation(
            action_id=action.id,
            language_id=action_translation['language_id'],
            name=action_translation['name'],
            description=action_translation['description'],
            short_description=action_translation['short_description']
        )
    return action


def parse_import_action(action_data, component):
    return import_action(parse_action(action_data), component)


def _parse_action_ref(action_data):
    if action_data is None:
        return None
    action_id = _get_id(action_data.get('action_id'))
    component_uuid = _get_uuid(action_data.get('component_uuid'))
    return {'action_id': action_id, 'component_uuid': component_uuid}


def _get_or_create_action_id(action_data):
    if action_data is None:
        return None
    component_id = _get_or_create_component_id(action_data['component_uuid'])
    try:
        action = get_action(action_data['action_id'], component_id)
    except errors.ActionDoesNotExistError:
        action = create_action(action_type_id=None, schema=None, fed_id=action_data['action_id'], component_id=component_id)
        fed_logs.create_ref_action(action.id, component_id)
    return action.id


def shared_action_preprocessor(action_id: int, _component: Component, refs: list, markdown_images: dict):
    action = get_action(action_id)
    if action.component_id is not None:
        return None
    translations_data = {}

    try:
        translations = get_action_translations_for_action(action_id)
        for translation in translations:
            description = translation.description
            markdown_as_html = markdown_to_html.markdown_to_safe_html(description)
            for file_name in find_referenced_markdown_images(markdown_as_html):
                markdown_image_b = get_markdown_image(file_name, None)
                description = description.replace('/markdown_images/' + file_name, '/markdown_images/' + flask.current_app.config['FEDERATION_UUID'] + '/' + file_name)
                if markdown_image_b is not None and file_name not in markdown_images:
                    markdown_images[file_name] = base64.b64encode(markdown_image_b).decode('utf-8')

            short_description = translation.short_description
            markdown_as_html = markdown_to_html.markdown_to_safe_html(short_description)
            for file_name in find_referenced_markdown_images(markdown_as_html):
                markdown_image_b = get_markdown_image(file_name, None)
                short_description = short_description.replace('/markdown_images/' + file_name, '/markdown_images/' + flask.current_app.config['FEDERATION_UUID'] + '/' + file_name)
                if markdown_image_b is not None and file_name not in markdown_images:
                    markdown_images[file_name] = base64.b64encode(markdown_image_b).decode('utf-8')

            lang_code = get_language(translation.language_id).lang_code
            translations_data[lang_code] = {
                'name': translation.name,
                'description': description,
                'short_description': short_description
            }
    except errors.ActionTranslationDoesNotExistError:
        translations_data = None

    if action.instrument_id is not None and ('instruments', action.instrument_id) not in refs:
        refs.append(('instruments', action.instrument_id))
    if action.user_id is not None and ('users', action.user_id) not in refs:
        refs.append(('users', action.user_id))
    if action.instrument_id is None:
        instrument = None
    else:
        i = get_instrument(action.instrument_id)
        if i.component_id is None:
            instrument = {
                'instrument_id': i.id,
                'component_uuid': flask.current_app.config['FEDERATION_UUID']
            }
        else:
            comp = i.component
            instrument = {
                'instrument_id': i.fed_id,
                'component_uuid': comp.uuid
            }
    if action.type.component_id is None:
        action_type = {
            'action_type_id': action.type.id,
            'component_uuid': flask.current_app.config['FEDERATION_UUID']
        }
    else:
        comp = get_component(action.type.component_id)
        action_type = {
            'action_type_id': action.type.fed_id,
            'component_uuid': comp.uuid
        }
    if ('action_types', action.type_id) not in refs:
        refs.append(('action_types', action.type_id))
    if action.user_id is None:
        user = None
    else:
        u = get_user(action.user_id)
        if u.component_id is None:
            user = {
                'user_id': u.id,
                'component_uuid': flask.current_app.config['FEDERATION_UUID']
            }
        else:
            comp = u.component
            user = {
                'user_id': u.fed_id,
                'component_uuid': comp.uuid
            }
    schema = action.schema.copy()
    schema_entry_preprocessor(schema, refs)
    return {
        'action_id': action.id if action.fed_id is None else action.fed_id,
        'component_uuid': flask.current_app.config['FEDERATION_UUID'] if action.component_id is None else action.component.uuid,
        'action_type': action_type,
        'instrument': instrument,
        'schema': schema,
        'user': user,
        'description_is_markdown': action.description_is_markdown,
        'is_hidden': action.is_hidden,
        'short_description_is_markdown': action.short_description_is_markdown,
        'translations': translations_data,
        'admin_only': action.admin_only,
        'disable_create_objects': action.disable_create_objects,
    }


def _parse_schema(schema, path=[]):
    if schema is None:
        return
    all_language_codes = {
        language.lang_code
        for language in get_languages()
    }
    for key in ['title', 'placeholder', 'default', 'note']:
        if key in schema and isinstance(schema[key], dict):
            for lang_code in list(schema[key].keys()):
                if lang_code not in all_language_codes:
                    del schema[key][lang_code]

    if 'languages' in schema and schema['languages'] != 'all':
        if not isinstance(schema['languages'], list):
            raise errors.InvalidDataExportError('Invalid schema')
        for language in schema['languages']:
            if language not in all_language_codes:
                schema['languages'].remove(language)

    if 'choices' in schema:
        for i, choice in enumerate(schema['choices']):
            if isinstance(choice, dict):
                for lang_code in list(choice.keys()):
                    if lang_code not in all_language_codes:
                        del choice[lang_code]
    if schema.get('type') == 'array' and 'items' in schema:
        _parse_schema(schema['items'], path + ['[?]'])
    if schema.get('type') == 'object':
        if isinstance(schema.get('properties'), dict):
            for property_name, property_schema in schema['properties'].items():
                _parse_schema(property_schema, path + [property_name])
                template = _get_dict(property_schema.get('template'))
                if template:
                    template_action = _parse_action_ref(template)
                    property_schema['template'] = template_action


def schema_entry_preprocessor(schema, refs):
    if type(schema) == list:
        for entry in schema:
            schema_entry_preprocessor(entry, refs)
    elif type(schema) == dict:
        if 'type' not in schema.keys():
            for key in schema:
                schema_entry_preprocessor(schema[key], refs)
        if schema.get('type') == 'object':
            if schema.get('template'):
                if ('actions', schema.get('template')) not in refs:
                    refs.append(('actions', schema.get('template')))
                action = get_action(schema.get('template'))
                if action.component_id is not None:
                    comp = action.component
                    schema['template'] = {
                        'action_id': action.fed_id,
                        'component_uuid': comp.uuid
                    }
                else:
                    schema['template'] = {
                        'action_id': action.id,
                        'component_uuid': flask.current_app.config['FEDERATION_UUID']
                    }
            for property in schema.get('properties'):
                schema_entry_preprocessor(schema['properties'][property], refs)
