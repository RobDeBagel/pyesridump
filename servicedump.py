#!/usr/local/bin/python
from esridump.dumper import EsriDumper
import simplejson as json
import argparse
import sys
import logging
import requests
import simplejson as json

def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Convert a whole Esri feature service URL to GeoJSON")
    parser.add_argument("url",
        help="Esri service URL")
    parser.add_argument("outdir",
        help="Output directory ")
    parser.add_argument("--jsonlines",
        action='store_true',
        default=False,
        help="Output newline-delimited GeoJSON Features instead of a FeatureCollection")
    parser.add_argument("-v", "--verbose",
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
        default=logging.INFO,
        help="Turn on verbose logging")
    parser.add_argument("-q", "--quiet",
        action='store_const',
        dest='loglevel',
        const=logging.WARNING,
        default=logging.INFO,
        help="Turn off most logging")
    parser.add_argument("-f", "--fields",
        help="Specify a comma-separated list of fields to request from the server")
    parser.add_argument("--no-geometry",
        dest='request_geometry',
        action='store_false',
        default=True,
        help="Don't request geometry for the feature so the server returns attributes only")
    parser.add_argument("-H", "--header",
        action='append',
        dest='headers',
        default=[],
        help="Add an HTTP header to send when requesting from Esri server")
    parser.add_argument("-p", "--param",
        action='append',
        dest='params',
        default=[],
        help="Add a URL parameter to send when requesting from Esri server")
    parser.add_argument("-o", "--offset",
        default=0,
        type=int,
        help="Layer index offset")

    return parser.parse_args(args)

def main():
    args = parse_args(sys.argv[1:]);
    logger = logging.getLogger('dumpService')
    logger.setLevel(args.loglevel)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    requested_fields = args.fields.split(',') if args.fields else None


    query_args = {'f': 'json'};

    response = requests.request('GET', args.url, params=query_args);
    layers = response.json().get('layers');

    for l in layers:
        if l.get('id') >= args.offset:
            print 'Layer: ' + str(l.get('id')) + ':' + l.get('name')
            sublayers = l.get('subLayerIds')
            print 'sublayers: '+ str(sublayers)
            if sublayers is None:
                outfile = open(args.outdir+'/'+l.get('name').replace(" ", "_")+'.json', "w")

                dumper = EsriDumper(args.url+'/'+str(l.get('id')),
                    extra_query_args=args.params,
                    extra_headers=args.headers,
                    fields=requested_fields,
                    request_geometry=args.request_geometry,
                    parent_logger=logger)
                if args.jsonlines:
                    for feature in dumper:
                        outfile.write(json.dumps(feature))
                        outfile.write('\n')
                else:
                    outfile.write('{"type":"FeatureCollection","features":[\n')
                    feature_iter = iter(dumper)
                    try:
                        feature = next(feature_iter)
                        while True:
                            outfile.write(json.dumps(feature))
                            feature = next(feature_iter)
                            outfile.write(',\n')
                    except StopIteration:
                        outfile.write('\n')
                    outfile.write(']}')
        else:
            print 'Skipping Layer ' + str(l.get('id'))




if __name__ == '__main__':
    main()

