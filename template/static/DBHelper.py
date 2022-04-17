__author__ = 'dev'
import logging
import psycopg2
import pdb

logging.basicConfig(filename='mdsbugs.log',level=logging.DEBUG)
logging.info('Start of DBHelper logging')

class DBHelper():

    #DBCONNECT = "dbname=mydefensiblespace user=postgres host=127.0.0.1 password=postgres"
    DBCONNECT = "dbname=mydefensiblespace user=postgres host=127.0.0.1 password=MyD#f#nsibl#9229"

    def __init__(self):
        pass

    def dbConnect(self):
        return psycopg2.connect(DBHelper.DBCONNECT)


    def dbExecute(self,sql):
        conn = psycopg2.connect(DBHelper.DBCONNECT)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        conn.close()
        return "success"

    def dbTransaction(self, sqls):
        conn = psycopg2.connect(DBHelper.DBCONNECT)
        cur = conn.cursor()
        try:
            for sql in sqls:
                print("execute",sql)
                cur.execute(sql)
            conn.commit()
            print("transaction succeeded")
        except Exception as e:
            print("transaction failed", str(e))
            conn.rollback()
            logging.error("Transaction api failed "+str(e))
        conn.close()

    def dbFetchOne(self,sql):
        conn = psycopg2.connect(DBHelper.DBCONNECT)
        cur = conn.cursor()
        cur.execute(sql)
        res = cur.fetchone()
        conn.close()
        return res

    def dbFetchAll(self,sql):
        conn = psycopg2.connect(DBHelper.DBCONNECT)
        cur = conn.cursor()
        cur.execute(sql)
        res = cur.fetchall()
        conn.close()
        return res

    def getData(self, sql):
        print("sql", sql)
        conn = psycopg2.connect(DBHelper.DBCONNECT)
        cur = conn.cursor()
        cur.execute(sql)
        # Retrieve the results of the query
        rows = cur.fetchall()
        #print(rows)
        conn.close()
        # Get the column names returned
        colnames = [desc[0] for desc in cur.description]
        # Find the index of the column that holds the geometry
        geomIndex = colnames.index("geometry")
        # output is the main content, rowOutput is the content from each record returned
        output = ""
        rowOutput = ""
        i = 0
        # For each row returned...
        while i < len(rows):
            # Make sure the geometry exists
            if rows[i][geomIndex] is not None:
                # If it's the first record, don't add a comma
                comma = "," if i > 0 else ""
                rowOutput = comma + '{"type": "Feature", "geometry": ' + rows[i][geomIndex] + ', "properties": {'
                properties = ""

                j = 0
                # For each field returned, assemble the properties object
                while j < len(colnames):
                    if colnames[j] != 'geometry':
                        comma = "," if j > 0 else ""
                        properties += comma + '"' + colnames[j] + '":"' + str(rows[i][j]) + '"'

                    j += 1

                rowOutput += properties + '}'
                rowOutput += '}'

                output += rowOutput

            # start over
            rowOutput = ""
            i += 1
        # with open(fileout + '.geojson', 'w') as outfile:
        #     outfile.write(totalOutput)
        #     outfile.close()
        # If a TopoJSON conversion is requested...
        #if arguments.topojson is True:
        #	topojson()
        #else:
        #    print("Done!")

        # Assemble the GeoJSON

        totalOutput = '{ "type": "FeatureCollection", "features": [ ' + output + ' ]}'

        #print("features", totalOutput)

        return totalOutput

    def getCityParcels(self, county, city, xcoord, ycoord):
        sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT GID, SIT_FULL_S, SIT_CITY, community, ST_AsGeoJSON(geom) as geometry
        FROM {}_parcels, pt as b
        WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(geom, b.geog, 280);""".format(xcoord, ycoord, county, city)
        return self.getData(sql)


    # This will need to use location query maybe
    def getStructures(self, county, city, xcoord, ycoord):
        sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT ST_AsGeoJSON(geom) as geometry
        FROM {}_bldgs_inter, pt as b
        WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(geom, b.geog, 300);""".format(xcoord, ycoord, county, city)
        return self.getData(sql)


    def getDefensibleSpace(self, county, city, xcoord, ycoord):
        sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT GID, fid_extend, ST_AsGeoJSON(geom) as geometry
        FROM {}_defensiblespace, pt as b
        WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(geom, b.geog, 3);""".format(xcoord, ycoord, county, city)
        return self.getData(sql)


    def getParcelData(self, county, address, city):
        sql = "SELECT GID, fid_extend, FID_Buildi, SIT_FULL_S, SIT_CITY, ST_AsGeoJSON(geom) as geometry FROM {}_defensiblespace WHERE UPPER(SIT_CITY) = '{}' and SIT_FULL_S = '{}'".format(county, city, address)
        return self.getData(sql)


    def getLocalAddressesNearby(self, county, city, xcoord, ycoord):  # used to populate table for Avery address labels
        sql = """
        WITH
           pt AS (
               SELECT ST_SetSRID(ST_MakePoint({},{}), 4326)::GEOGRAPHY AS geog
           )
        SELECT SIT_FULL_S, SIT_CITY, SIT_STATE, community
        FROM {}_parcels, pt as b
        WHERE UPPER(SIT_CITY) = '{}' and ST_DWithin(geom, b.geog, 300);""".format(xcoord, ycoord, county, city)
        return self.getData(sql)


    def getMDSCommunity(self, county, city, mdscommunity):  # link for outside url to open map page rendering the map of community

        sql = """SELECT SIT_FULL_S, xcoord, ycoord, ST_AsGeoJSON(geom) as geometry
        FROM {}_parcels WHERE UPPER(SIT_CITY) = '{}' and UPPER(community) = '{}' ORDER BY SIT_FULL_S;""".format(county, city.upper(), mdscommunity.upper())
        communityParcels = self.getData(sql)


        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {0}_zone5 WHERE UPPER(SIT_CITY) = '{1}' and SIT_FULL_S
        IN (SELECT SIT_FULL_S FROM {0}_parcels WHERE UPPER(SIT_CITY) = '{1}' and UPPER(community) = '{2}'); """.format(county, city.upper(), mdscommunity.upper())
        zone5geos = self.getData(sql)

        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {0}_zone30 WHERE UPPER(SIT_CITY) = '{1}' and SIT_FULL_S
        IN (SELECT SIT_FULL_S FROM {0}_parcels WHERE UPPER(SIT_CITY) = '{1}' and UPPER(community) = '{2}'); """.format(county, city.upper(), mdscommunity.upper())
        print("test zone30")

        zone30geos = self.getData(sql)

        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {0}_zone100 WHERE UPPER(SIT_CITY) = '{1}' and SIT_FULL_S
        IN (SELECT SIT_FULL_S FROM {0}_parcels WHERE UPPER(SIT_CITY) = '{1}' and UPPER(community) = '{2}'); """.format(county, city.upper(), mdscommunity.upper())
        zone100geos = self.getData(sql)

        return {'parcels':communityParcels,'zone5':zone5geos, 'zone30':zone30geos, 'zone100':zone100geos}


    def getMDSCommunity2(self, county, city, mdscommunity):  # link for outside url to open map page rendering the map of community

        sql = """SELECT SIT_FULL_S, xcoord, ycoord, ST_AsGeoJSON(geom) as geometry
        FROM {}_parcels WHERE UPPER(SIT_CITY) = '{}' and UPPER(community) = '{}' ORDER BY SIT_FULL_S;""".format(county, city.upper(), mdscommunity.upper())
        communityParcels = self.getData(sql)


        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {}_zone5 WHERE UPPER(SIT_CITY) = '{}'
        and UPPER(community) = '{}'); """.format(county, city.upper(), mdscommunity.upper())
        zone5geos = self.getData(sql)

        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {}_zone30 WHERE UPPER(SIT_CITY) = '{}'
        and UPPER(community) = '{}'); """.format(county, city.upper(), mdscommunity.upper())
        zone5geos = self.getData(sql)

        zone30geos = self.getData(sql)

        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {}_zone100 WHERE UPPER(SIT_CITY) = '{}'
        and UPPER(community) = '{}'); """.format(county, city.upper(), mdscommunity.upper())
        zone100geos = self.getData(sql)

        return {'parcels':communityParcels,'zone5':zone5geos, 'zone30':zone30geos, 'zone100':zone100geos}



    def getCountyFirewiseCommunity(self, county, firewise):  # link for outside url to open map page rendering the map of community

        sql = """SELECT SIT_FULL_S, xcoord, ycoord, ST_AsGeoJSON(geom) as geometry
        FROM {}_parcels WHERE community = '{}' ORDER BY SIT_FULL_S;""".format(county, firewise)
        communityParcels = self.getData(sql)

        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {0}_zone5 WHERE UPPER(SIT_CITY) = '{1}' and SIT_FULL_S
        IN (SELECT SIT_FULL_S FROM {0}_parcels WHERE  UPPER(community) = '{1}'); """.format(county, firewise.upper())
        zone5geos = self.getData(sql)

        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {0}_zone30 WHERE UPPER(SIT_CITY) = '{1}' and SIT_FULL_S
        IN (SELECT SIT_FULL_S FROM {0}_parcels WHERE UPPER(community) = '{1}'); """.format(county , firewise.upper())
        print("test zone30")

        zone30geos = self.getData(sql)

        sql = """SELECT status, ST_AsGeoJSON(geom) as geometry FROM {0}_zone100 WHERE SIT_FULL_S
        IN (SELECT SIT_FULL_S FROM {0}_parcels WHERE  UPPER(community) = '{1}'); """.format(county, firewise.upper())
        zone100geos = self.getData(sql)



        return {'parcels':communityParcels,'zone5':zone5geos, 'zone30':zone30geos, 'zone100':zone100geos}



    # def getCityParcels(self, county, city, xcoord, ycoord):
    #     sql = "SELECT GID, SIT_FULL_S, SIT_CITY, community, ST_AsGeoJSON(geom) as geometry FROM {}_parcels WHERE UPPER(SIT_CITY) =\
    #      '{}' and ST_DWithin(geom, ST_MakePoint({},{})::geography, 200);".format(county,  city, xcoord, ycoord)
    #     #sql = "SELECT GID, SIT_FULL_S, SIT_CITY, community, ST_AsGeoJSON(geom) as geometry FROM {}_parcels WHERE UPPER(SIT_CITY) = '{}'".format(county, city)
    #     return self.getData(sql)
    #
    # # This will need to use location query maybe
    # def getStructures(self, county, city, xcoord, ycoord):
    #     sql = "SELECT ST_AsGeoJSON(geom) as geometry FROM {}_bldgs_inter WHERE UPPER(SIT_CITY) =\
    #      '{}' and ST_DWithin(geom, ST_MakePoint({},{})::geography, 250);".format(county,  city, xcoord, ycoord)
    #     #sql = "SELECT GID, fid_extend, SIT_FULL_S, SIT_CITY, ST_AsGeoJSON(geom) as geometry FROM {}_bldgs_inter WHERE UPPER(SIT_CITY) = '{}'".format(county, city)
    #     return self.getData(sql)



    # def getDefensibleSpace(self, county, city, xcoord, ycoord):
    #     sql = "SELECT GID, fid_extend, ST_AsGeoJSON(geom) as geometry FROM {}_defensiblespace WHERE UPPER(SIT_CITY) =\
    #      '{}' and ST_DWithin(geom, ST_MakePoint({},{})::geography, 200);".format(county,  city, xcoord, ycoord)
    #     #sql = "SELECT GID, fid_extend, ST_AsGeoJSON(geom) as geometry FROM {}_defensiblespace WHERE UPPER(SIT_CITY) = '{}'".format(county, city)
    #     return self.getData(sql)


        # TODO: BELOW IS QUICKER - MAYBE BECAUE IT DOESN"T HAVE MAKEPOINT
    # SELECT GID, fid_extend, ST_AsGeoJSON(geom) as geometry FROM Placer_defensiblespace WHERE UPPER(SIT_CITY) = 'COLFAX'
    # and ST_DWithin(geom,(SELECT geom FROM Placer_parcels WHERE UPPER(SIT_CITY) = 'COLFAX' and UPPER(SIT_FULL_S) = '23235 TOKAYANA WAY')::geography, 200);

    # OR BETTER
    #     WITH
    #        pt AS (
    #            SELECT ST_SetSRID(ST_MakePoint(-120.969103486,39.0828868), 4326)::GEOGRAPHY AS geog
    #        )
    #
    #     SELECT GID, fid_extend, ST_AsGeoJSON(geom) as geometry
    #     FROM Placer_defensiblespace, pt as b
    #     WHERE UPPER(SIT_CITY) = 'COLFAX' and ST_DWithin(geom, b.geog, 200);
