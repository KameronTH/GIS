#Kameron H
#4/30/22
#Description: Use field names to map bus routes

#Import relavent modules and variables
import arcpy
aoi = r"C:\Users\Kameron\Desktop\ArcGIS\Projects\MLK_River\Park_Improvements\Park_Improvements.gdb\AOI_Extended"
bus_stops = r"C:\Users\Kameron\Desktop\ArcGIS\Projects\MLK_River\Park_Improvements\Park_Improvements.gdb\Mata_Stops"
spatial_ref = arcpy.Describe(aoi).spatialReference

#Need to make a new field based on the first line of the stop_names field
arcpy.management.AddField(bus_stops, "First_Road_Stop", "TEXT")

#Update new field with name of main street that bus drives along using ArcPy Update Cursor
with arcpy.da.UpdateCursor(bus_stops, ["stop_name","First_Road_Stop"]) as cursor: 
    for row in cursor:
        row[1] = row[0].partition('@')[0]
        cursor.updateRow(row)