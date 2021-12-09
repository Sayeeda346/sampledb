# coding: utf-8

import contextlib
import getpass
import io
import json
import os
import shutil
import sys
import tempfile
import time

import flask
from PIL import Image
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

import chromedriver_binary

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import sampledb
import sampledb.config
import sampledb.logic
import tests.conftest

DEVICE_PIXEL_RATIO = int(os.environ.get('DEVICE_PIXEL_RATIO', '1'))


def scroll_to(driver, x, y):
    driver.execute_script("window.scrollTo({}, {})".format(x, y))
    # disable scrollbars
    driver.execute_script("""
    var style = document.createElement('style');
    style.innerHTML = '::-webkit-scrollbar { display: none; }';
    var head = document.getElementsByTagName('head')[0];
    head.appendChild(style);
    """)
    return driver.execute_script("""
    return window.pageYOffset;
    """)


def resize_for_screenshot(driver, width, height):
    """
    Resize the webdriver window to make screenshots match a given size.

    Webdrivers like Chrome might display information bars at the top that will
    result in a screenshot size smaller than the window size. This function
    iteratively compensates for these decorations until the screenshot size
    matches the requested width and height.

    :param driver: the webdriver
    :param width: the requested width
    :param height: the requested height
    :return:
    """
    global previous_width_correction
    global previous_height_correction
    real_height = -1
    real_width = -1
    requested_width = width
    requested_height = height
    width_correction = previous_width_correction
    height_correction = previous_height_correction
    while real_height != height or real_width != width:
        requested_width += width_correction
        requested_height += height_correction
        if requested_width <= 0 or requested_height <= 0:
            break
        driver.set_window_size(requested_width, requested_height)
        image_data = driver.get_screenshot_as_png()
        real_width, real_height = Image.open(io.BytesIO(image_data)).size
        width_correction = width - real_width
        height_correction = height - real_height
    previous_width_correction = requested_width - width
    previous_height_correction = requested_height - height


# Cached values for resize_for_screenshot()
previous_height_correction = 0
previous_width_correction = 0


def guest_invitation(base_url, driver):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'users/invitation')
    for heading in driver.find_elements_by_tag_name('h1'):
        if 'Invite' in heading.text:
            break
    else:
        assert False
    container = driver.find_element_by_id('main').find_elements_by_class_name('container')[-1]
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/guest_invitation.png', (0, heading.location['y'], width, min(heading.location['y'] + max_height, container.location['y'] + container.rect['height'])))


def default_permissions(base_url, driver):
    width = 1280
    min_height = 200
    resize_for_screenshot(driver, width, min_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'users/me/preferences')
    for heading in driver.find_elements_by_tag_name('h2'):
        if 'Default Permissions' in heading.text:
            break
    else:
        assert False
    for next_heading in driver.find_elements_by_tag_name('h2'):
        if 'Other Settings' in next_heading.text:
            break
    else:
        assert False
    scroll_to(driver, 0, heading.location['y'])
    resize_for_screenshot(driver, width, next_heading.location['y'] - heading.location['y'])
    driver.get_screenshot_as_file('docs/static/img/generated/default_permissions.png')


def action(base_url, driver, action):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'actions/{}'.format(action.id))
    heading = driver.find_elements_by_tag_name('h1')[0]

    for anchor in driver.find_elements_by_tag_name('a'):
        if 'Create Sample' in anchor.text:
            break
    else:
        assert False
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/action.png', (0, heading.location['y'], width, min(heading.location['y'] + max_height, anchor.location['y'] + anchor.rect['height'])))


def tags_input(base_url, driver, object):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'objects/{}'.format(object.id))
    for row in driver.find_elements_by_class_name('row'):
        if 'Tags' in row.text:
            break
    else:
        assert False
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/tags.png', (0, row.location['y'], width, min(row.location['y'] + max_height, row.location['y'] + row.rect['height'])))


def comments(base_url, driver, object):
    sampledb.logic.comments.create_comment(object.id, user.id, "This is an example comment.")
    sampledb.logic.comments.create_comment(object.id, user.id, "Comments can contain multiple paragraphs.\nThe text will be displayed as you typed it.\n - As a result, you can use simple lists.\n - Markdown or similar languages are not supported however.")

    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'objects/{}'.format(object.id))
    for heading in driver.find_elements_by_tag_name('h2'):
        if 'Comments' in heading.text:
            break
    else:
        assert False
    y_offset = scroll_to(driver, 0, heading.location['y'])
    comment_form = driver.find_element_by_id('new-comment-form')
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/comments.png', (0, heading.location['y'] - y_offset, width, min(heading.location['y'] + max_height, comment_form.location['y'] + comment_form.rect['height']) - y_offset))


def activity_log(base_url, driver, object):
    object = sampledb.logic.objects.create_object(object.action_id, object.data, user.id, object.id)
    sampledb.logic.files.create_local_file(object.id, user.id, "example.txt", lambda stream: stream.write(b'example text'))
    sampledb.logic.comments.create_comment(object.id, user.id, "This is an example comment.")

    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'objects/{}'.format(object.id))
    for heading in driver.find_elements_by_tag_name('h2'):
        if 'Activity Log' in heading.text:
            break
    else:
        assert False
    y_offset = scroll_to(driver, 0, heading.location['y'])
    activity_log = driver.find_element_by_id('activity_log')
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/activity_log_dontblock.png', (0, heading.location['y'] - y_offset, width, min(activity_log.location['y'] - y_offset + activity_log.rect['height'], max_height)))


def locations(base_url, driver, object):
    object = sampledb.logic.objects.create_object(object.action_id, object.data, user.id, object.id)
    campus = sampledb.logic.locations.create_location({"en": "Campus A"}, {"en": ""}, None, user.id)
    b048 = sampledb.logic.locations.create_location({"en": "Building 1"}, {"en": ""}, campus.id, user.id)
    r139b = sampledb.logic.locations.create_location({"en": "Room 42"}, {"en": ""}, b048.id, user.id)
    sampledb.logic.locations.assign_location_to_object(object.id, r139b.id, None, user.id, {"en": "Shelf C"})

    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'objects/{}'.format(object.id))
    for heading in driver.find_elements_by_tag_name('h2'):
        if 'Location' in heading.text:
            break
    else:
        assert False
    y_offset = scroll_to(driver, 0, heading.location['y'])
    location_form = driver.find_element_by_id('assign-location-form')
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/locations.png', (0, heading.location['y'] - y_offset, width, min(heading.location['y'] + max_height, location_form.location['y'] + location_form.rect['height']) - y_offset))


def unread_notification_icon(base_url, driver):
    sampledb.logic.notifications.create_other_notification(user.id, "This is an example notification.")

    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url)
    navbar = driver.find_element_by_class_name('navbar-static-top')
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/unread_notification_icon.png', (0, navbar.location['y'], width, min(navbar.location['y'] + max_height, navbar.location['y'] + navbar.rect['height'])))
    notification = sampledb.logic.notifications.get_notifications(user_id=user.id)[0]
    sampledb.logic.notifications.delete_notification(notification.id)


def files(base_url, driver, object):
    object = sampledb.logic.objects.create_object(object.action_id, object.data, user.id, object.id)
    sampledb.logic.files.create_local_file(object.id, user.id, "example.txt", lambda stream: stream.write(b'example text'))
    sampledb.logic.files.create_local_file(object.id, user.id, "notes.pdf", lambda stream: stream.write(b'example text'))
    with open('docs/utils/photo.jpg', 'rb') as image_file:
        sampledb.logic.files.create_local_file(object.id, user.id, "photo.jpg", lambda stream: stream.write(image_file.read()))

    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'objects/{}'.format(object.id))
    for heading in driver.find_elements_by_tag_name('h2'):
        if 'Files' in heading.text:
            break
    else:
        assert False
    for form_group in driver.find_elements_by_class_name('form-group'):
        if 'Upload' in form_group.text:
            break
    else:
        assert False
    y_offset = scroll_to(driver, 0, heading.location['y'])
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/files.png', (0, heading.location['y'] - y_offset, width, min(heading.location['y'] + max_height, form_group.location['y'] + form_group.rect['height']) - y_offset))


def file_information(base_url, driver, object):
    object = sampledb.logic.objects.create_object(object.action_id, object.data, user.id, object.id)
    sampledb.logic.files.create_local_file(object.id, user.id, "notes.pdf", lambda stream: stream.write(b'example text'))
    sampledb.logic.files.update_file_information(object.id, 0, user.id, 'Scanned Notes', 'This is an example file.')

    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'objects/{}'.format(object.id))
    file_table = driver.find_element_by_id('file_table')
    file_table.find_elements_by_class_name('button-file-info')[0].click()

    modal = driver.find_element_by_id('fileInfoModal-0').find_element_by_class_name('modal-content')

    # Wait for modal to be visible
    time.sleep(10)

    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/file_information.png', (0, modal.rect['y'], width, min(modal.rect['y'] + max_height, modal.rect['y'] + modal.rect['height'])))


def labels(base_url, driver, object):
    width = 640
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'objects/{}/label#toolbar=0'.format(object.id))

    # Wait for PDF preview to be visible
    time.sleep(10)

    driver.get_screenshot_as_file('docs/static/img/generated/labels.png')


def hazards_input(base_url, driver, action):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    driver.get(base_url + 'objects/new?action_id={}'.format(action.id))
    for form_group in driver.find_elements_by_class_name('form-group'):
        if len(form_group.find_elements_by_class_name('ghs-hazards-selection')) > 0:
            break
    else:
        assert False
    for label in form_group.find_elements_by_tag_name('label'):
        if 'Environmental' in label.text:
            break
    else:
        assert False
    label.click()
    for label in form_group.find_elements_by_tag_name('label'):
        if 'Corrosive' in label.text:
            break
    else:
        assert False
    label.click()
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/hazards_input.png', (0, form_group.location['y'], width, min(form_group.location['y'] + max_height, form_group.location['y'] + form_group.rect['height'])))


def object_permissions(base_url, driver):
    width = 1280
    min_height = 200
    resize_for_screenshot(driver, width, min_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))

    driver.get(base_url + 'objects/{}/permissions'.format(object.object_id))
    resize_for_screenshot(driver, width, min_height)
    for heading in driver.find_elements_by_tag_name('h2'):
        if 'Permissions' in heading.text:
            break
    else:
        assert False
    scroll_to(driver, 0, heading.location['y'])
    footer = driver.find_elements_by_tag_name('footer')[-1]
    resize_for_screenshot(driver, width, footer.location['y'] - heading.location['y'])
    driver.get_screenshot_as_file('docs/static/img/generated/object_permissions.png')


def advanced_search_by_property(base_url, driver, object):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))

    driver.get(base_url + 'objects/{}'.format(object.id))
    for row in driver.find_elements_by_class_name('row'):
        if 'Name' in row.text:
            break
    else:
        assert False

    driver.execute_script("var helpers = document.getElementsByClassName('search-helper'); for(var i = 0; i < helpers.length; i++) {helpers[i].style.opacity = 1;}")
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/advanced_search_by_property.png', (0, row.location['y'], width, min(row.location['y'] + max_height, row.location['y'] + row.rect['height'])))


def advanced_search_visualization(base_url, driver):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))

    driver.get(base_url + 'objects/?q=%22Sb%22+in+substance+and+%28temperature+%3C+110degC+or+temperature+%3E+120degC%29&advanced=on')
    search_tree = driver.find_element_by_id('search-tree')

    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/advanced_search_visualization.png', (0, search_tree.location['y'], width, min(search_tree.location['y'] + max_height, search_tree.location['y'] + search_tree.rect['height'])))


def schema_editor(base_url, driver):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))

    driver.get(base_url + 'actions/new/')
    form = driver.find_element_by_id('schema-editor')
    y_offset = scroll_to(driver, 0, form.location['y'])
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/schema_editor.png', (0, form.location['y'] - y_offset, width, form.location['y'] - y_offset + min(max_height, form.rect['height'])))


def disable_schema_editor(base_url, driver):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + f'users/{user.id}/autologin')

    driver.get(base_url + f'users/{user.id}/preferences')
    radio_button = driver.find_element_by_id('input-use-schema-editor-yes')
    parent = radio_button.find_element_by_xpath('./..')
    while parent is not None:
        if parent.get_attribute('class') == 'form-group':
            form = parent
            break
        else:
            parent = parent.find_element_by_xpath('./..')
    else:
        assert False
    y_offset = scroll_to(driver, 0, form.location['y'])
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/disable_schema_editor.png', (0, form.location['y'] - y_offset, width, form.location['y'] - y_offset + min(max_height, form.rect['height'])))


def translations(base_url, driver):
    width = 1280
    max_height = 1000
    resize_for_screenshot(driver, width, max_height)
    driver.get(base_url + 'users/{}/autologin'.format(user.id))
    for language in sampledb.logic.languages.get_languages():
        if not language.enabled_for_input:
            sampledb.logic.languages.update_language(
                language_id=language.id,
                names=language.names,
                lang_code=language.lang_code,
                datetime_format_datetime=language.datetime_format_datetime,
                datetime_format_moment=language.datetime_format_moment,
                enabled_for_input=True,
                enabled_for_user_interface=True
            )

    driver.get(base_url + 'actions/new/')
    driver.execute_script("""
    $('[data-name="input-names"] .selectpicker').selectpicker('val', ['-99', '-98']);
    $('[data-name="input-names"] .selectpicker').change();
    """)
    form = driver.find_element_by_css_selector('[data-name="input-names"]')
    y_offset = scroll_to(driver, 0, form.location['y'])
    save_cropped_screenshot_as_file(driver, 'docs/static/img/generated/translations.png', (0, form.location['y'] - y_offset, width, form.location['y'] - y_offset + min(max_height, form.rect['height'])))


def save_cropped_screenshot_as_file(driver, file_name, box):
    image_data = driver.get_screenshot_as_png()
    image = Image.open(io.BytesIO(image_data))
    if box:
        image = image.crop([c * DEVICE_PIXEL_RATIO for c in box])
    image.save(file_name)


temp_dir = tempfile.mkdtemp()
try:
    os.mkdir(os.path.join(temp_dir, 'uploaded_files'))
    sampledb.config.FILE_STORAGE_PATH = os.path.join(temp_dir, 'uploaded_files')
    app = tests.conftest.create_app()
    with app.app_context():
        user = sampledb.models.User(
            name="Example User",
            email="example@example.com",
            type=sampledb.models.UserType.PERSON
        )
        sampledb.db.session.add(user)
        sampledb.db.session.commit()
        assert user.id is not None

        other_user = sampledb.models.User(
            name="Other User",
            email="example@example.com",
            type=sampledb.models.UserType.PERSON
        )
        sampledb.db.session.add(other_user)
        sampledb.db.session.commit()
        assert other_user.id is not None

        group = sampledb.logic.groups.create_group(
            name={"en": "Example Group"},
            description={"en": "An example group for the documentation"},
            initial_user_id=user.id
        )

        project = sampledb.logic.projects.create_project(
            name={"en": "Example Project"},
            description={"en": "An example project for the documentation"},
            initial_user_id=user.id
        )

        instrument = sampledb.logic.instruments.create_instrument()
        sampledb.logic.instrument_translations.set_instrument_translation(sampledb.models.Language.ENGLISH,
                                                                          instrument.id,
                                                                          name="Example Instrument",
                                                                          description="This is an example instrument for the documentation.")
        schema = {
            'title': "Sample Information",
            'type': 'object',
            'properties': {
                'name': {
                    'title': 'Sample Name',
                    'type': 'text'
                },
                'tags': {
                    'title': 'Tags',
                    'type': 'tags'
                },
                'hazards': {
                    'title': 'GHS Hazards',
                    'type': 'hazards'
                }
            },
            'required': ['name', 'hazards'],
            'propertyOrder': ['name', 'tags', 'hazards']
        }
        instrument_action = sampledb.logic.actions.create_action(
            action_type_id=sampledb.models.ActionType.SAMPLE_CREATION,
            schema=schema,
            instrument_id=instrument.id
        )

        sampledb.logic.action_translations.set_action_translation(
            sampledb.models.Language.ENGLISH,
            instrument_action.id,
            name="Sample Creation",
            description="This is an example action"
        )
        sampledb.logic.action_permissions.set_action_public(instrument_action.id)
        data = {
            'name': {
                '_type': 'text',
                'text': 'Demo Sample'
            },
            'tags': {
                '_type': 'tags',
                'tags': ['demo', 'other_tag', 'ombe-1']
            },
            'hazards': {
                '_type': 'hazards',
                'hazards': [5, 9]
            }
        }
        object = sampledb.logic.objects.create_object(
            action_id=instrument_action.id,
            data=data,
            user_id=user.id,
            previous_object_id=None,
            schema=schema
        )

        os.makedirs('docs/static/img/generated', exist_ok=True)
        options = Options()
        # disable Chrome sandbox for root in GitLab CI
        if 'CI' in os.environ and getpass.getuser() == 'root':
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
        with contextlib.contextmanager(tests.conftest.create_flask_server)(app) as flask_server:
            with contextlib.closing(Chrome(options=options)) as driver:
                time.sleep(5)
                object_permissions(flask_server.base_url, driver)
                default_permissions(flask_server.base_url, driver)
                guest_invitation(flask_server.base_url, driver)
                action(flask_server.base_url, driver, instrument_action)
                hazards_input(flask_server.base_url, driver, instrument_action)
                tags_input(flask_server.base_url, driver, object)
                comments(flask_server.base_url, driver, object)
                activity_log(flask_server.base_url, driver, object)
                files(flask_server.base_url, driver, object)
                file_information(flask_server.base_url, driver, object)
                labels(flask_server.base_url, driver, object)
                advanced_search_by_property(flask_server.base_url, driver, object)
                advanced_search_visualization(flask_server.base_url, driver)
                locations(flask_server.base_url, driver, object)
                schema_editor(flask_server.base_url, driver)
                unread_notification_icon(flask_server.base_url, driver)
                disable_schema_editor(flask_server.base_url, driver)
                translations(flask_server.base_url, driver)
finally:
    shutil.rmtree(temp_dir)
