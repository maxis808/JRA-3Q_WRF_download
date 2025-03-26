import pandas as pd
import numpy as np
import netCDF4 as nc
import os
import requests


def round_down_day(number):
    return int((np.floor((number - 1) / 5) * 5) + 1)


def round_up_day(number):
    return int(np.ceil(number / 5) * 5)


def write_record(file, data, field, date, units, desc, level=200100.0, fill=-1e30):
    a = np.array([4], dtype='>i4')
    a.tofile(file)
    version = np.array([5], dtype='>i4')
    version.tofile(file)
    a = np.array([4], dtype='>i4')
    a.tofile(file)
    a = np.array([156], dtype='>i4')
    a.tofile(file)

    date = date.strftime('%Y-%m-%d_%H:00:00')
    date = date.ljust(24)
    hdate = np.array([date], dtype='S24')
    hdate.tofile(file)

    xfcst = np.array([0], dtype='>f4')
    xfcst.tofile(file)

    map_source = 'JRA-3Q'
    map_source = map_source.ljust(32)
    map_source = np.array([map_source], dtype='S32')
    map_source.tofile(file)

    field = field.ljust(9)
    field = np.array([field], dtype='S9')
    field.tofile(file)

    units = units.ljust(25)
    units = np.array([units], dtype='S25')
    units.tofile(file)

    desc = desc.ljust(46)
    desc = np.array([desc], dtype='S46')
    desc.tofile(file)

    xlvl = np.array([level], dtype='>f4')
    xlvl.tofile(file)

    ny, nx = np.shape(data)
    nx = np.array([nx], dtype='>i4')
    ny = np.array([ny], dtype='>i4')
    nx.tofile(file)
    ny.tofile(file)

    iproj = np.array([4], dtype='>i4')
    iproj.tofile(file)

    a = np.array([156], dtype='>i4')
    a.tofile(file)
    a = np.array([28], dtype='>i4')
    a.tofile(file)

    startloc = 'SWCORNER'
    startloc = np.array([startloc], dtype='S8')
    startloc.tofile(file)

    startlat = np.array([89.71324], dtype='>f4')
    startlat.tofile(file)

    startlon = np.array([0.0], dtype='>f4')
    startlon.tofile(file)

    nlats = np.array([240.0], dtype='>f4')
    nlats.tofile(file)

    deltalon = np.array([0.375], dtype='>f4')
    deltalon.tofile(file)

    earth_radius = np.array([6371], dtype='>f4')
    earth_radius.tofile(file)

    a = np.array([28], dtype='>i4')
    a.tofile(file)
    a = np.array([4], dtype='>i4')
    a.tofile(file)
    a = np.array([0], dtype='>i4')
    a.tofile(file)
    a = np.array([4], dtype='>i4')
    a.tofile(file)
    a = np.array([np.size(data)*4], dtype='>i4')
    a.tofile(file)

    data[data > 1e10] = fill
    data = np.array(data, dtype='>f4')
    data.tofile(file)

    a = np.array([np.size(data)*4], dtype='>i4')
    a.tofile(file)


def download(start_date, end_date, pref='', porosity=0.43, output_path='', save_path='', var_path=''):
    try:
        all_vars = np.loadtxt(var_path + 'JRA_names.txt', dtype=str, delimiter=',')
    except:
        raise Exception('Can\'t find model variable file')

    try:
        start_date = pd.to_datetime(start_date, dayfirst=True)
        end_date = pd.to_datetime(end_date, dayfirst=True)
    except:
        raise Exception('Couldn\'t parse the date. Make sure date is in dd-MM-yy hh:mm format.')

    if end_date < start_date:
        raise Exception('End date is earlier than the start date')

    dates = pd.date_range(start=start_date, end=end_date, freq='6h')
    beginning = pd.to_datetime('1900-01-01 00:00:00')

    for date in dates:
        for f_nr in range(len(all_vars)):
            level = all_vars[f_nr, 0]
            var_code = all_vars[f_nr, 1]
            variable = all_vars[f_nr, 2]

            match level:
                case 'bnd_ocean':
                    st_date = date.strftime('%Y%m0100')
                    en_date = date.strftime('%Y%m')+str(date.days_in_month)+'23'
                    date_start_end = st_date + '_' + en_date
                case 'anl_surf' | 'anl_land':
                    st_date = date.strftime('%Y%m0100')
                    en_date = date.strftime('%Y%m') + str(date.days_in_month) + '18'
                    date_start_end = st_date + '_' + en_date
                case 'anl_p':
                    st_day = round_down_day(date.day)
                    if st_day == 26:
                        en_day = date.days_in_month
                    else:
                        en_day = round_up_day(date.day)

                    st_date = date.strftime('%Y%m') + "{:02d}".format(st_day) + '00'
                    en_date = date.strftime('%Y%m') + "{:02d}".format(en_day) + '18'
                    date_start_end = st_date + '_' + en_date

            filename = ('jra3q.{}.{}.{}.{}.nc').format(level, var_code, variable, date_start_end)

            f = os.path.join(save_path, filename)
            if not os.path.isfile(f):
                res = False
                while not res:
                    try:
                        session = requests.Session()
                        url = ('https://thredds.rda.ucar.edu/thredds/fileServer/files/g/d640000/' +
                               '{}/{}/{}'.format(level, date.strftime('%Y%m'), filename))
                        print('Fetching {}'.format(url))
                        response = session.get(url)
                        with open(f, 'wb') as ff:
                            ff.write(response.content)
                        res = True
                    except:
                        print('Couldn\'t download the file. Check your connection or filename. Retrying...')

            with nc.Dataset(f) as df:
                hours_since = round((date-beginning).total_seconds() / 3600)
                df_time = np.array(df['time'])
                time_index = np.where(df_time == hours_since)[0][0]
                data = np.array(df[variable][time_index])

                match variable:
                    case "gp-sfc-cn-gauss":
                        gp = np.array(data)
                    case "land-sfc-cn-gauss":
                        lsm = np.array(data)
                    case "soilvic-bg-an-gauss":
                        depth = np.array(df['depth_below_land_surface'])
                        soilvic = np.array(data)
                    case "liqvsm-bg-an-gauss":
                        liqvsm = np.array(data)
                    case "soiltmp-bg-an-gauss":
                        soiltmp = np.array(data)
                    case "tsg-sfc-an-gauss":
                        tsg = np.array(data)
                    case "tmp-pres-an-gauss":
                        pressure = (np.array(df['pressure_level'])*100)
                        tmp = np.array(data)
                    case "rh-pres-an-gauss":
                        rh = np.array(data)
                    case "ugrd-pres-an-gauss":
                        ugrd = np.array(data)
                    case "vgrd-pres-an-gauss":
                        vgrd = np.array(data)
                    case "hgt-pres-an-gauss":
                        hgt = np.array(data)
                    case "tmp2m-hgt-an-gauss":
                        tmp2m = np.array(data)
                    case "rh2m-hgt-an-gauss":
                        rh2m = np.array(data)
                    case "weasd-sfc-an-gauss":
                        weasd = np.array(data)
                    case "ugrd10m-hgt-an-gauss":
                        ugrd10m = np.array(data)
                    case "vgrd10m-hgt-an-gauss":
                        vgrd10m = np.array(data)
                    case "pres-sfc-an-gauss":
                        pres = np.array(data)
                    case "prmsl-msl-an-gauss":
                        prmsl = np.array(data)
                    case "icec-sfc-fc-gauss":
                        icec = np.array(data)
                    case "wtmp-sfc-fc-gauss":
                        wtmp = np.array(data)

        f = os.path.join(var_path+"geopotential.nc")
        try:
            with nc.Dataset(f) as df:
                variable = "gp-sfc-cn-gauss"
                data = np.array(df[variable][0])
                gp = np.array(data)
        except:
            raise Exception('Can\'t find geopotential.nc file')

        f = os.path.join(var_path+"landmask.nc")
        try:
            with nc.Dataset(f) as df:
                variable = "land-sfc-cn-gauss"
                data = np.array(df[variable][0])
                lsm = np.array(data)
        except:
            raise Exception('Can\'t find landmask.nc file')

        time = date

        filename = output_path + pref + date.strftime('%Y-%m-%d_%H')
        if not os.path.isfile(filename):
            with open(filename, "ab") as file:
                write_record(file, wtmp, 'SST', time, 'K', 'Sea surface temperature')
                write_record(file, icec, 'SEAICE', time, 'fraction', 'Sea-Ice-Fraction')
                write_record(file, tmp2m, 'TT', time, 'K', 'Temperature')
                write_record(file, prmsl, 'PMSL', time, 'Pa', 'Sea-level Pressure')
                write_record(file, pres, 'PSFC', time, 'Pa', 'Surface Pressure')
                write_record(file, ugrd10m, 'UU', time, 'm s-1', 'U')
                write_record(file, vgrd10m, 'VV', time, 'm s-1', 'V')
                write_record(file, weasd, 'SNOW', time, 'kg m-2', 'Water Equivalent of Accumulated Snow Depth')
                write_record(file, rh2m, 'RH', time, '%', 'Relative Humidity')
                write_record(file, tsg, 'SKINTEMP', time, 'K', 'Skin temperature')
                write_record(file, (liqvsm[0] + soilvic[0])*porosity, 'SM000002', time, 'm3 m-3', 'Soil moisture of 0-2 cm ground layer')
                write_record(file, (liqvsm[1] + soilvic[1])*porosity, 'SM002007', time, 'm3 m-3', 'Soil moisture of 2-7 cm ground layer')
                write_record(file, (liqvsm[2] + soilvic[2])*porosity, 'SM007019', time, 'm3 m-3', 'Soil moisture of 7-19 cm ground layer')
                write_record(file, (liqvsm[3] + soilvic[3])*porosity, 'SM019049', time, 'm3 m-3', 'Soil moisture of 19-49 cm ground layer')
                write_record(file, (liqvsm[4] + soilvic[4])*porosity, 'SM049099', time, 'm3 m-3', 'Soil moisture of 49-99 cm ground layer')
                write_record(file, (liqvsm[5] + soilvic[5])*porosity, 'SM099199', time, 'm3 m-3', 'Soil moisture of 99-199 cm ground layer')
                write_record(file, (liqvsm[6] + soilvic[6])*porosity, 'SM199349', time, 'm3 m-3', 'Soil moisture of 199-349 cm ground layer')
                write_record(file, soiltmp[0], 'ST000002', time, 'K', 'T of 0-2 cm ground layer')
                write_record(file, soiltmp[1], 'ST002007', time, 'K', 'T of 2-7 cm ground layer')
                write_record(file, soiltmp[2], 'ST007019', time, 'K', 'T of 7-19 cm ground layer')
                write_record(file, soiltmp[3], 'ST019049', time, 'K', 'T of 19-49 cm ground layer')
                write_record(file, soiltmp[4], 'ST049099', time, 'K', 'T of 49-99 cm ground layer')
                write_record(file, soiltmp[5], 'ST099199', time, 'K', 'T of 99-199 cm ground layer')
                write_record(file, soiltmp[6], 'ST199349', time, 'K', 'T of 199-349 cm ground layer')
                write_record(file, gp/9.80665, 'SOILHGT', time, 'm', 'Terrain field of source analysis')
                write_record(file, lsm, 'LANDSEA', time, '0/1 Flag', 'Land/Sea flag')
                for n, h in enumerate(pressure):
                    write_record(file, tmp[n], 'TT', time, 'K', 'Temperature', level=h)
                    write_record(file, ugrd[n], 'UU', time, 'm s-1', 'U', level=h)
                    write_record(file, vgrd[n], 'VV', time, 'm s-1', 'V', level=h)
                    write_record(file, hgt[n], 'HGT', time, 'm', 'Height', level=h)
                    write_record(file, rh[n], 'RH', time, '%', 'Relative Humidity', level=h)

if __name__ == "__main__":
    download('01-01-2000 00:00', '01-01-2000 18:00', var_path='C:\\Users\\mp\\Documents\\JRA-3q\\',
             save_path="C:\\Users\\\mp\\\Documents\\\JRA-3q\\netcdf\\",
             output_path="C:\\Users\\mp\\Documents\\JRA-3q\\output\\")