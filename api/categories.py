import xmlrpclib

import tornadorpc
from tornado.web import HTTPError
from bson.objectid import ObjectId

from api import auth
from models import Post, Category, EmbeddedCategory


class Categories(object):
    @tornadorpc.async
    @auth
    def wp_getCategories(self, blogid, user, password):
        # TODO: cache
        wp_categories = []

        def got_category(category, error):
            if error:
                raise error
            elif category:
                wp_categories.append(Category(**category).to_wordpress(self.application))
            else:
                # Done
                self.result(wp_categories)

        self.settings['db'].categories.find().sort([('name', 1)]).each(
            got_category)

    @tornadorpc.async
    @auth
    def mt_getPostCategories(self, postid, user, password):
        def got_post(post, error):
            if error:
                raise error
            if not post:
                self.result(xmlrpclib.Fault(404, "Not found"))
            else:
                self.result([
                    cat.to_metaweblog(self.application)
                    for cat in Post(**post).categories
                ])

        self.settings['db'].posts.find_one(
            {'_id': ObjectId(postid)}, callback=got_post)

    @tornadorpc.async
    @auth
    def wp_newCategory(self, blogid, user, password, struct):
        def inserted_category(_id, error):
            if error:
                raise error

            self.result(str(_id))

        category = Category.from_wordpress(struct)
        self.settings['db'].categories.insert(
            category.to_python(), callback=inserted_category)

    @tornadorpc.async
    @auth
    def mt_setPostCategories(self, postid, user, password, categories):
        embedded_cats = [
            EmbeddedCategory.from_metaweblog(cat).to_python()
            for cat in categories]

        def set_post_categories(result, error):
            if error:
                raise error

            self.result(result['n'] == 1)

        self.settings['db'].posts.update(
            {'_id': ObjectId(postid)},
            {'$set': {'categories': embedded_cats}},
            callback=set_post_categories
        )
