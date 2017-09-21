prjDir = pwd;
ge_out = [];

% Set the center of the map we want to look at.
desiredLon = 37.734082;
desiredLat = 55.786976;

%%
% This is the only thing that should be hardcoded for each city
% Chages may be needed for non-round cities (efficiency)
% Kremlin-centered URL for yandex maps
z=14;
refX = 309; refY = 160;
centerLat = 55.755768;
centerLon = 37.617671;

%%
% the rule between tile length and z is as simple as that:
% 1 - each zoom in divides 1 tile into 4 and vice versa
% 2 - when z=9, the tile side is 44 km long
tileLen = 44 * 2^(9-z); % in km basically

% If z is odd, the map center is between four tiles,
% if z is even, the map center is in the center of one tile

% For the custom map piece
stepsInX = sign(centerLon - desiredLon) * round(lon_to_m(centerLon - desiredLon, desiredLat)/tileLen/1e3);
stepsInY = sign(desiredLat - centerLat) * round(lat_to_m(centerLat - desiredLat, desiredLat)/tileLen/1e3);

centerX = refX * 2^(z-9)  + (z+(z-9)/2)*(rem(z,2) == 0) + stepsInX + (2*(z-9)+0.5)*(rem(z,2) ~= 0);
centerY = refY * 2^(z-9)  + (z+(z-9)/2)*(rem(z,2) == 0) + stepsInY + (2*(z-9)+0.5)*(rem(z,2) ~= 0);

span = 1;

% Preallocate the matrix
trafficData = zeros(256*length(ceil(centerX-span):floor(centerX+span)), ...
    256*length(ceil(centerY-span):floor(centerY+span)));
latMtrx = trafficData; lonMtrx = trafficData;
x_count = 0;

% Loop for tiles grabbing and analysis
for x = floor(centerX-span-1):floor(centerX+span)
    y_count = 0;
    for y = floor(centerY-span-1):floor(centerY+span)

        % Form the wget string and download the tile
        wgetBase = '"http://jgo.maps.yandex.net/1.1/tiles?l=trf&lang=ru_RU&';
        wgetEnding = 'tm=1372673624"';
        wgetX = ['x=' num2str(x, '%2.3i') '&']; %618
        wgetY = ['y=' num2str(y, '%2.3i') '&']; %312
        wgetZ = ['z=' num2str(z, '%2.3i') '&'];
        wgetString = [wgetBase wgetX wgetY wgetZ wgetEnding];

        % System-dependent wget call
        if(strfind(computer, 'WIN'))
            system([fullfile(prjDir, 'wget.exe') ' -q -O ' fullfile(prjDir, 'tiles', ['tile_' num2str(x, '%2.3i') '_' num2str(y, '%2.3i') '.png'] ...
                ) ' ' wgetString]);
        else
            system(['wget -q -O ' fullfile(prjDir, 'tiles', ['tile_' num2str(x, '%2.3i') '_' num2str(y, '%2.3i') '.png'] ...
                 ) ' ' wgetString]);
        end

        % Got the file, grab the image and divide it by colors
        tp = (imread(fullfile(prjDir, 'tiles', ['tile_' num2str(x, '%2.3i') '_' num2str(y, '%2.3i') '.png']), 'png'));
        tp_r = (squeeze(tp(:,:,1)));
        tp_g = (squeeze(tp(:,:,2)));
        tp_b = (squeeze(tp(:,:,3)));

        % Get the coordinates for the current tile
        % The cases are different for different elevationtypes: even and odd issue again
        a = round(x-centerX);
        if((rem(z,2) == 0))
            lat1 = desiredLat + round(centerY-y)*m_to_lat(tileLen*1e3, desiredLat) - sign(centerY-y)*m_to_lat(tileLen*1e3, desiredLat)-m_to_lat(tileLen*1e3, desiredLat);
            lat2 = desiredLat + round(centerY-y)*m_to_lat(tileLen*1e3, desiredLat)-m_to_lat(tileLen*1e3, desiredLat);
            lon1 = desiredLon + round(x-centerX)*m_to_lon(tileLen*1e3, desiredLat) - sign(x-centerX)*m_to_lon(tileLen*1e3, desiredLat)+m_to_lon(tileLen*1e3, desiredLat);
            lon2 = desiredLon + round(x-centerX)*m_to_lon(tileLen*1e3, desiredLat)+m_to_lon(tileLen*1e3, desiredLat);
        else
            lat1 = desiredLat + (sign((centerY-y))-(centerY==y))*abs(m_to_lat(tileLen*1e3/2+tileLen*1e3*(abs(centerY-y)-1), desiredLat))-m_to_lat(tileLen*1e3, desiredLat);
            lat2 = desiredLat + (sign((centerY-y))+(centerY==y))*abs(m_to_lat(tileLen*1e3/2 + tileLen*1e3*abs(centerY-y), desiredLat))-m_to_lat(tileLen*1e3, desiredLat);
            lon1 = desiredLon + (sign((x-centerX))-(centerX==x))*abs(m_to_lon(tileLen*1e3/2+tileLen*1e3*(abs(x-centerX)-1), desiredLat))+m_to_lon(tileLen*1e3, desiredLat);
            lon2 = desiredLon + (sign((x-centerX))+(centerX==x))*abs(m_to_lon(tileLen*1e3/2 + tileLen*1e3*abs(x-centerX),desiredLat))+m_to_lon(tileLen*1e3, desiredLat);
        end

        % Latitude is inverted since it has inverted direction with y
        lat = linspace(max(lat1, lat2), min(lat1, lat2), size(tp, 1));
        lon = linspace(min(lon1, lon2), max(lon1, lon2), size(tp, 2));

        % Yandex traffic colors are indexed badly which is likely a trick.
        indGreen = tp_g <= 240 & tp_g >= 150 & tp_r <=150; % more or less
        indYellow = tp_g <= 210 & tp_g >= 170 & tp_r <= 255 & tp_r >= 210 & tp_b < 10; % revision needed
        indRed = tp_g <= 100 & tp_b <= 100 & tp_r >=240; % more or less
        indDarkRed = []; % Not reviewed
        indBlocked = []; % Not reviewed

        mtrxPiece = zeros(size(tp_r));
        mtrxPiece(indGreen) = 0.25; mtrxPiece(indYellow) = 0.5; mtrxPiece(indRed) = 0.75;
        trafficData((y_count*256+1):(y_count+1)*256, ...
            (x_count*256+1):(x_count+1)*256) = mtrxPiece;

        latMtrx((y_count*256+1):(y_count+1)*256, ...
            (x_count*256+1):(x_count+1)*256) = repmat(lat, [256 1])';
        lonMtrx((y_count*256+1):(y_count+1)*256, ...
            (x_count*256+1):(x_count+1)*256) = repmat(lon, [256 1]);;

        figure(z); hold on; imagesc(tp, 'XData', lon, 'YData', lat); %xlim([centerLon-0.4 centerLon+0.4]); ylim([centerLat-0.4 centerLat+0.4]);

        y_count = y_count+1;
    end
    x_count = x_count+1;
end

% Do the matrices dump into the files
currTime = datevec(now);

fdata = fopen(fullfile(prjDir, 'data', ['MoscowTraffic-' num2str(currTime(3), '%2.2i') num2str(currTime(2), '%2.2i') num2str(currTime(1)-2e3, '%2.2i') '-' ...
        num2str(currTime(4), '%2.2i') num2str(currTime(5), '%2.2i') num2str(floor(currTime(6)), '%2.2i') '_no_zeros.dat']),'w');

for i = 1:size(trafficData, 1)
    for j = 1:size(trafficData, 1)
        if(trafficData(i,j)~=0)
            fprintf(fdata, '%f %f %f\n', lonMtrx(i,j), latMtrx(i,j), trafficData(i,j));
        end      
    end  
end
fclose(fdata);