# wrapper code for easier handling of ONIX files:
#
# OnixHandler -- a sax ContentHandler that produces a stream of ONIX "product" data in xmltramp objects
#
# OnixProduct -- a wrapper for the objects produced by OnixHandler, providing human-friendly field access
# (mostly just providing a dictionary interface where long ("reference") names can be used even when the
# data is encoded with opaque ("short") names.)

from xml.sax.handler import *

from .sax_utils import *
from .xmltramp import *

repo_path = os.getenv("PHAROS_REPO")
codelists_path = f"{repo_path}/catalog/onix/ONIX_BookProduct_CodeLists.xsd"
ref_dtd_path = f"{repo_path}/catalog/onix/ONIX_BookProduct_Release2.1_reference.xsd"

# for testing, also set URL_CACHE_DIR; see bottom.

onix_codelists = None
onix_shortnames = None


def init():
    f = open(codelists_path)
    onix_codelists = parse_codelists(f)
    f.close()
    f = open(ref_dtd_path)
    onix_shortnames = parse_shortnames(f)
    f.close()


class OnixProduct:
    # N.B.: this only works when using the "short" names of elements.
    # we should check that the document uses the short DTD, and if not,
    # use the reference names to access field values.

    def __init__(self, p):
        self.p = p

    @staticmethod
    def reify_child(v):
        if len(v._dir) == 1 and isinstance(v._dir[0], StringTypes):
            return v._dir[0]
        else:
            return OnixProduct(v)

    def __getitem__(self, n):
        slicing = False
        if isinstance(n, SliceType):
            slicing = True
            reference_name = n.start
        else:
            reference_name = n
        name = OnixProduct.get_shortname(reference_name)  # or reference_name.lower ()
        values = self.p[name:]
        if slicing:
            return map(OnixProduct.reify_child, values)
        else:
            if len(values) == 0:
                raise KeyError(f"no value for {reference_name} ({name})")
            elif len(values) > 1:
                raise Exception(f"more than one value for {reference_name} ({name})")
            return OnixProduct.reify_child(values[0])

    def get(self, n):
        try:
            return self.__getitem__(n)
        except KeyError:
            return None

    def getLineNumber(self):
        return self.p.getLineNumber()

    def __unicode__(self):
        return self.p.__unicode__()

    def __str__(self):
        return self.__unicode__()

    def pi_type_name(code):
        return onix_codelists["List5"][code][0]

    @staticmethod
    def contributor_role(code):
        return onix_codelists["List17"][code][0]

    @staticmethod
    def get_shortname(reference_name):
        try:
            return onix_shortnames[reference_name]
        except KeyError:
            raise Exception(f"unknown reference name: {reference_name}")


class OnixHandler(ContentHandler):
    def __init__(self, parser, receiver):
        self.parser = parser
        self.receiver = receiver
        self.subhandler = None
        ContentHandler.__init__(self)

    def startElementNS(self, name, qname, attrs):
        if self.subhandler:
            self.subhandler.startElementNS(name, qname, attrs)
            self.subdepth += 1
        else:
            (uri, localname) = name
            if localname == "product":
                self.subhandler = xmltramp.Seeder(self.parser)
                self.subhandler.startElementNS(name, qname, attrs)
                self.subdepth = 1

    def endElementNS(self, name, qname):
        if self.subhandler:
            self.subhandler.endElementNS(name, qname)
            self.subdepth -= 1
            if self.subdepth == 0:
                self.receiver(self.subhandler.result)
                self.subhandler = None

    def characters(self, content):
        if self.subhandler:
            self.subhandler.characters(content)


def parse_shortnames(input):
    def schema(name, attrs):
        def element(name, attrs):
            def typespec(name, attrs):
                def attribute(name, attrs):
                    if attrs.getValueByQName("name") == "shortname":
                        shortname = attrs.getValueByQName("fixed")
                        return CollectorValue(shortname)
                    else:
                        return CollectorNone()

                return NodeCollector({"attribute": attribute, collector_any: typespec})

            elt_name = attrs.getValueByQName("name")
            return NamedCollector(elt_name, {collector_any: typespec})

        return DictCollector({"element": element})

    return collector_parse(input, {"schema": schema})


def parse_codelists(input):
    def schema(name, attrs):
        def simpleType(name, attrs):
            def restriction(name, attrs):
                def enumeration(name, attrs):
                    def annotation(name, attrs):
                        def documentation(name, attrs):
                            return TextCollector()

                        return ListCollector({"documentation": documentation})

                    return NamedCollector(
                        attrs.getValueByQName("value"), {"annotation": annotation}
                    )

                return DictCollector({"enumeration": enumeration})

            return NamedCollector(
                attrs.getValueByQName("name"), {"restriction": restriction}
            )

        return DictCollector({"simpleType": simpleType})

    return collector_parse(input, {"schema": schema})


init()

### testing

from xml.sax.saxutils import prepare_input_source


class TestErrorHandler:
    def error(self, exn):
        raise exn

    def fatalError(self, exn):
        raise exn

    def warning(self, exn):
        sys.stderr.write(f"warning: {exn.getMessage}\n")


def produce_items(input, produce):
    source = prepare_input_source(input)

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 1)
    parser.setContentHandler(OnixHandler(parser, process_item))
    url_cache_dir = os.getenv("URL_CACHE_DIR")
    if url_cache_dir:
        sys.stderr.write(f"using url cache in {url_cache_dir}\n")
        parser.setEntityResolver(CachingEntityResolver(parser, url_cache_dir))
    else:
        sys.stderr.write(
            "no url_cache_dir; XML resources will always be loaded from network\n"
        )
    parser.setErrorHandler(TestErrorHandler())
    parser.parse(source)


def process_item(i):
    print(OnixProduct(i))


if __name__ == "__main__":
    from sys import stdin

    print("Reading ONIX data from standard input ...")
    produce_items(stdin, process_item)
