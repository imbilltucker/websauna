"""Map URL traversing ids to database ids and vice versa."""
from pyramid_web20.utils import slug


class Mapper:
    """Define mapping interface used by CRUD subsystem."""

    def get_path_from_object(self, obj):
        """Map database object to an travesable URL path."""
        raise NotImplementedError()

    def get_id_from_path(self, path):
        """Map traversable resource name to an database object id."""
        raise NotImplementedError()


class IdMapper(Mapper):
    """Use object/column attribute id to map functions.

    By default this is set to use integer ids, but you can override properties.
    """

    #: What is the object attibute name defining the its id
    mapping_attribute = "id"

    #: Function to translate obj attribute -> URL path str
    transform_to_path = str

    #: Function to translate URL path str -> object id
    transform_to_id = int

    #: is_id(path) function checks whether the given URL path should be mapped to object and is a valid object id. Alternatively, if the path doesn't look like an object id, it could be a view name. Because Pyramid traversing checks objects prior views, we need to let bad object ids to fall through through KeyError, so that view matching mechanism kicks in. By default we check for number integer id.
    #: Some object paths cannot be reliable disquished from view names, like UUID strings. In this case ``is_id`` is None, the lookup always first goes to the database. The database item is not with view name a KeyError is triggerred and thus Pyramid continues to view name resolution. This behavior is suboptimal and may change in the future versions
    is_id = staticmethod(lambda value: value.isdigit())

    def __init__(self, mapping_attribute=None, transform_to_path=None, transform_to_id=None, is_id=None):
        if mapping_attribute:
            self.mapping_attribute = mapping_attribute

        if transform_to_path:
            self.transform_to_path = transform_to_path

        if transform_to_id:
            self.transform_to_id = transform_to_id

        if is_id:
            self.is_id = is_id

    def get_path_from_object(self, obj):
        """Map database object to an travesable URL path."""
        return self.transform_to_path(getattr(obj, self.mapping_attribute))

    def get_id_from_path(self, path):
        return self.transform_to_id(path)


class Base64UUIDMapper(IdMapper):
    """Map objects to URLs using their UUID property."""

    #: Override this if you want to change the column name containing uuid
    mapping_attribute = "uuid"

    #: Use utils.slug package to produce B64 strings from UUIDs
    transform_to_id = slug.uuid_to_slug

    #: Use utils.slug package to produce B64 strings from UUIDs
    transform_to_path = slug.slug_to_uuid

    #: We cannot validate beforehand if a string is valid UUID object id or not, we always resolve to a database lookup
    is_id = lambda x: True
