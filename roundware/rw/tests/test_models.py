from django.test import TestCase
from django.conf import settings

from model_mommy import mommy
from model_mommy.generators import gen_file_field

from roundware.rw import models
from roundware.settings import DEFAULT_SESSION_ID

from .common import use_locmemcache


def rw_validated_file_field_gen():
    return gen_file_field()


class RWTestCase(TestCase):
    """ provide common testcase data for roundware.rw test cases 
    """

    def setUp(self):
        self.maxDiff = None

        generator_dict = {
            'roundware.rw.fields.RWValidatedFileField': 
            rw_validated_file_field_gen
        }
        # can't set this directly in settings: db ENGINE not yet available
        setattr(settings, 'MOMMY_CUSTOM_FIELDS_GEN', generator_dict)


class TestMasterUI(RWTestCase):
    """ exercise MasterUI model class """

    def setUp(self):
        super(type(self), TestMasterUI).setUp(self)

        # make masterui, makes our tagcategory, uimode, project, 
        # selectionmethod
        self.masterui = mommy.make('rw.MasterUI')
        self.other_uimode = mommy.make('rw.UIMode')
        self.project = self.masterui.project

    @use_locmemcache(models, 'cache')
    def test_tag_category_cache_invalidation_post_save(self):
        """ test that cached value for tag categories for the MasterUI's mode
        is invalidated after MasterUI saved.
        """
        ui_mode_name = self.masterui.ui_mode.name
        get_orig_tag_cats = self.project.get_tag_cats_by_ui_mode(ui_mode_name)

        # is original tag_cat of masterui returned by Project's method
        self.assertIn(self.masterui.tag_category, get_orig_tag_cats)

        # change the ui mode of our masterui
        self.masterui.ui_mode = self.other_uimode

        # should still get old tag categories... cached
        get_tag_cats = self.project.get_tag_cats_by_ui_mode(ui_mode_name)
        self.assertIn(self.masterui.tag_category, get_tag_cats)

        # save the masterui, now should not get old tag categories... 
        # cached copy invalidated
        self.masterui.save()
        get_tag_cats = self.project.get_tag_cats_by_ui_mode(ui_mode_name)
        self.assertNotIn(self.masterui.tag_category, get_tag_cats)


class TestProject(RWTestCase):

    def setUp(self):
        super(type(self), TestProject).setUp(self)
        self.project = mommy.make('rw.Project')
        self.ui_mode = mommy.make('rw.UIMode')

    def test_no_tag_cats_returned_new_project(self):
        """ test no tag_categories returned for a new project with no masterui
        """
        cats = self.project.get_tag_cats_by_ui_mode(self.ui_mode.name)
        self.assertTrue(len(cats) == 0)

    def test_correct_tag_cats_returned(self):
        """ test that we get correct tagcategories for our project once
            we add a MasterUI.
        """
        masterui = mommy.make('rw.MasterUI', project=self.project, 
                              ui_mode=self.ui_mode)
        cats = self.project.get_tag_cats_by_ui_mode(self.ui_mode.name)
        self.assertIn(masterui.tag_category, cats)

    def test_no_tag_cats_returned_wrong_uimode(self):
        """ test no tag_categories returned if we specify a uimode that 
            is not connected to project via a MasterUI
        """
        other_ui_mode = mommy.make('rw.UIMode', name='bogus')
        other_master_ui = mommy.make('rw.MasterUI', project=self.project,
                                     ui_mode=other_ui_mode)
        cats = self.project.get_tag_cats_by_ui_mode(self.ui_mode.name)
        self.assertNotIn(other_master_ui.tag_category, cats)


class TestAsset(RWTestCase):

    def setUp(self):
        super(type(self), TestAsset).setUp(self)

        self.session1 = mommy.make('rw.Session', id=DEFAULT_SESSION_ID)
        self.session2 = mommy.make('rw.Session')
        self.project = mommy.make('rw.Project')
        self.asset1 = mommy.make('rw.Asset')
        self.asset2 = mommy.make('rw.Asset')
        self.vote1 = mommy.make('rw.Vote', session=self.session1, 
                                asset=self.asset1, type="like")
        self.vote2 = mommy.make('rw.Vote', session=self.session2, 
                                asset=self.asset1, type="like")
        self.vote3 = mommy.make('rw.Vote', session=self.session1, 
                        asset=self.asset2, type="like")
        self.vote4 = mommy.make('rw.Vote', session=self.session1, 
                        asset=self.asset1, type="flag")


    def test_get_likes(self):
        self.assertEquals(2, self.asset1.get_likes())
        self.assertEquals(1, self.asset2.get_likes())

    def test_get_flags(self):
        self.assertEquals(1, self.asset1.get_flags())
