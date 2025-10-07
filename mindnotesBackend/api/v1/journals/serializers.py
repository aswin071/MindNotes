from rest_framework import serializers
from journals.models import Tag, JournalEntry


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at', 'updated_at']


class JournalEntrySerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'title', 'content', 'entry_type', 'entry_date', 'privacy',
            'is_favorite', 'is_archived', 'tags', 'location_name', 'latitude',
            'longitude', 'weather', 'temperature', 'word_count', 'character_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['word_count', 'character_count', 'created_at', 'updated_at']

    def _upsert_tags(self, user, tags_data):
        tag_objs = []
        for tag in tags_data or []:
            tag_obj, _ = Tag.objects.get_or_create(user=user, name=tag.get('name'), defaults={'color': tag.get('color', '#3B82F6')})
            if tag.get('color') and tag_obj.color != tag['color']:
                tag_obj.color = tag['color']
                tag_obj.save(update_fields=['color'])
            tag_objs.append(tag_obj)
        return tag_objs

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        user = self.context['request'].user
        entry = JournalEntry.objects.create(user=user, **validated_data)
        if tags_data:
            entry.tags.set(self._upsert_tags(user, tags_data))
        return entry

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if tags_data is not None:
            instance.tags.set(self._upsert_tags(instance.user, tags_data))
        return instance


